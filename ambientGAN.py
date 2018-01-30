import tensorflow as tf

from ops import *
from architecture import *
from measurement import *

class ambientGAN():
    def __init__(self, args):
        self.batch_size = args.batch_size
        self.input_dim = args.input_dim 

        self.images, self.data_count = load_train_data(args)
        self.build_model()
        self.build_loss()

        #summary
        self.d_loss_sum = tf.summary.scalar("d_loss", self.d_loss) 
        self.g_loss_sum = tf.summary.scalar("g_loss", self.g_loss)
        self.images_sum = tf.summary.image("input_img", self.images)
        self.genX_sum = tf.summary.image("genX", self.genX)

    def build_model(self):
        batch_z = tf.random_uniform([self.batch_size, self.input_dim], minval=-1, maxval=1, dtype=tf.float32)
        self.genX, self.g_nets = self.generator(batch_z, name="generator")

        self.fake_measureY = self.measurement_fn(self.genX, name="measurement_fn")
        self.fake_d_logits, self.fake_d_net = self.discriminator(self.fake_measureY, name="discriminator")
        self.real_d_logits, self.real_d_net = self.discriminator(self.images, name="discriminator", reuse=True)


        trainable_vars = tf.trainable_variables()
        self.g_vars = []
        self.d_vars = []
        for var in trainable_vars:
            if "generator" in var.name:
                self.g_vars.append(var)
            else:
                self.d_vars.append(var)

    def build_loss(self):
        def calc_loss(logits, label):
            if label==1:
                y = tf.ones_like(logits)
            else:
                y = tf.zeros_like(logits)
            return tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=logits, labels=y))

        self.real_d_loss = calc_loss(self.real_d_logits, 1)
        self.fake_d_loss = calc_loss(self.fake_d_logits, 0)

        self.d_loss = self.real_d_loss + self.fake_d_loss
        self.g_loss = calc_loss(self.fake_d_logits, 1)



    def generator(self, z, name="generator"):
        nets = []
        with tf.variable_scope(name) as scope:
            linear_l = linear(z, 8*4*4*64, name="linear")
            reshaped = tf.reshape(linear_l, shape=[-1, 4, 4, 8*64])
            init_layer = batch_norm(reshaped, name="bn0")
            init_layer = tf.nn.relu(init_layer)

            deconv1 = deconv2d(init_layer, [self.batch_size, 8, 8, 256], name="deconv1")

            deconv1 = batch_norm(deconv1, name="bn1")
            deconv1 = tf.nn.relu(deconv1)
            nets.append(deconv1)

            deconv2 = deconv2d(deconv1, [self.batch_size, 16, 16, 128], name="deconv2")
            deconv2 = batch_norm(deconv2, name="bn2")
            deconv2 = tf.nn.relu(deconv2)
            nets.append(deconv2)

            deconv3 = deconv2d(deconv2, [self.batch_size, 32, 32, 64], name="deconv3")
            deconv3 = batch_norm(deconv3, name="bn3")
            deconv3 = tf.nn.relu(deconv3)
            nets.append(deconv3)

            deconv4 = deconv2d(deconv3, [self.batch_size, 64, 64, 3], name="deconv4")
            deconv4 = tf.nn.tanh(deconv4)
            nets.append(deconv4)

            return deconv4, nets

    def discriminator(self, input, name="discriminator", reuse=False):
        nets = []
        with tf.variable_scope(name, reuse=reuse) as scope:
            conv1 = tf.contrib.layers.conv2d(input, 64, 5, 2,
                                     padding="VALID",
                                     activation_fn=None,
                                     scope="conv1")
            conv1 = batch_norm(conv1, name="bn1")
            conv1 = tf.nn.relu(conv1)
            nets.append(conv1)

            conv2 = tf.contrib.layers.conv2d(conv1, 128, 5, 2,
                                     padding="VALID",
                                     activation_fn=None,
                                     scope="conv2")
            conv2 = batch_norm(conv2, name="bn2")
            conv2 = tf.nn.relu(conv2)
            nets.append(conv2)

            conv3 = tf.contrib.layers.conv2d(conv2, 256, 5, 2,
                                     padding="VALID",
                                     activation_fn=None,
                                     scope="conv3")
            conv3 = batch_norm(conv1, name="bn3")
            conv3 = tf.nn.relu(conv3)
            nets.append(conv3)

            conv4 = tf.contrib.layers.conv2d(conv3, 512, 5, 2,
                                     padding="VALID",
                                     activation_fn=None,
                                     scope="conv4")
            conv4 = batch_norm(conv4, name="bn4")                                                                                                                           
            conv4 = tf.nn.relu(conv4)
            nets.append(conv4)

            flatten = tf.contrib.layers.flatten(conv4)

            output = linear(flatten, 1, name="linear")


            return output, nets



    def measurement_fn(self, input, name="measurement_fn"):
        with tf.variable_scope(name) as scope:
            return block_pixels(input, p=0.5)
            return block_patch(input, 16)












