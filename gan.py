import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np

class Gan():
    '''
    A class to implement a Generative Adversarial Network

    input:
    - generator: a keras model that will be used as generator
    - discriminator: a keras model that will be used as discriminator
    - input_shape: a tuple that specifies the shape of the generator input
    '''
    def __init__(self, generator, discriminator, input_shape):
        # Input checks
        if not(generator.input.shape[1:] == input_shape):
            raise Exception("generator input shape doesn't match input_shape")
        if not(generator.output.shape[1:] == discriminator.input.shape[1:]):
            raise Exception("generator output shape doesn't match discriminator input shape")
        if not(discriminator.output.shape[1:] ==(1,)):
            raise Exception("discriminator output is not binary")

        self.discriminator = discriminator
        self.generator = generator
        self.input_shape = input_shape
        self.gan = None

        self.build_gan()


    def build_gan(self):

        # Feeds noise input to generator and generate image
        z = layers.Input(shape=self.input_shape)
        img = self.generator(z)

        # Sets discriminator not trainable because this will be used to train the generator only,
        # training of the discriminator is done separately
        self.discriminator.trainable = False

        # Discriminator gets the generated image as input and predicts if it's original or generated
        valid = self.discriminator(img)

        # Gan is the combined model obtained by stacking generator and discriminator
        self.gan = models.Model(z, valid)
        self.gan.compile(loss='binary_crossentropy',
                         optimizer=tf.keras.optimizers.RMSprop(lr=0.0002, rho=0.9))


    def train(self, X_train, epochs, batch_size=128, save_interval=50):
        # input checks
        if not isinstance(batch_size, int):
            raise ValueError("batch_size is not an integer")
        if not isinstance(save_interval, int):
            raise ValueError("save_interval is not an integer")

        half_batch_size = int(batch_size / 2)

        for epoch in range(epochs):
            # 1. Train discriminator with 50% of batch being real images and 50% generated images
            # 2. Train the generator

            # Discriminator
            # Select a random half the batch size of images
            idx = np.random.randint(0, X_train.shape[0], half_batch_size)
            imgs = X_train[idx]

            noise = np.random.normal(0, 1, (half_batch_size,)+self.input_shape)

            # Generate a half batch of new images
            gen_imgs = self.generator.predict(noise)

            # Train the discriminator
            d_loss_real = self.discriminator.train_on_batch(imgs, np.ones((half_batch_size, 1)))
            d_loss_fake = self.discriminator.train_on_batch(gen_imgs, np.zeros((half_batch_size, 1)))
            d_loss = np.mean([d_loss_real, d_loss_fake], 0)

            # Generator
            # We use the whole GAN model, we feed random noise and we want the generated images to be labeled as
            # valid (1)
            noise = np.random.normal(0, 1, (batch_size,)+self.input_shape)

            valid_y = np.array([1] * batch_size)

            # Train the generator
            g_loss = self.gan.train_on_batch(noise, valid_y)

            # Print the progress
            print("epoch: {} [D loss: {}, acc.: {:.2f}] [G loss: {}]".format(epoch, d_loss[0], 100 * d_loss[1], g_loss))

            # If at save interval => save generated image samples
            if epoch % save_interval == 0:
                self.save_generator(epoch)
                self.save_discriminator(epoch)

        # Saving final models
        self.save_generator("final")
        self.save_discriminator("final")


    def save_generator(self, epoch):
        self.generator.save('generator_{}.hdf5'.format(epoch))


    def save_discriminator(self, epoch):
        self.discriminator.save('discriminator_{}.hdf5'.format(epoch))

