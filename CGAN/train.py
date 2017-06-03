from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data
import numpy as np

import time
import cgan
import image_utils as iu


dirs = {
    'sample_output': './CGAN/',
    'checkpoint': './model/checkpoint',
    'model': './model/CGAN-model.ckpt'
}
paras = {
    'global_step': 1000001,
    'logging_interval': 10000
}


def main():
    start_time = time.time()  # clocking start

    # mnist data loading
    mnist = input_data.read_data_sets('./MNIST_data', one_hot=True)

    # GPU configure
    # gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=1)
    # config = tf.ConfigProto(allow_soft_placement=True, gpu_options=gpu_options)
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    with tf.Session(config=config) as s:
        # GAN Model
        model = cgan.CGAN(s)

        # initializing
        s.run(tf.global_variables_initializer())

        sample_x, _ = mnist.train.next_batch(model.sample_num)
        sample_y = np.zeros(shape=[model.sample_num, model.y_dim])
        sample_y[:, 3] = 1   # specify label number what u wanna get
        sample_z = np.random.uniform(-1., 1., [model.sample_num, model.z_dim]).astype(np.float32)

        d_overpowered = False
        for step in range(paras['global_step']):
            batch_x, batch_y = mnist.train.next_batch(model.batch_size)
            batch_z = np.random.uniform(-1., 1., size=[model.batch_size, model.z_dim]).astype(np.float32)

            # update D network
            if not d_overpowered:
                _, d_loss = s.run([model.d_op, model.d_loss], feed_dict={model.x: batch_x,
                                                                         model.c: batch_y,
                                                                         model.z: batch_z})

            # update G network
            _, g_loss = s.run([model.g_op, model.g_loss], feed_dict={model.c: batch_y,
                                                                     model.z: batch_z})

            if step % paras['logging_interval'] == 0:
                batch_x, batch_y = mnist.test.next_batch(model.batch_size)
                batch_z = np.random.uniform(-1., 1., [model.batch_size, model.z_dim]).astype(np.float32)

                d_loss, g_loss, summary = s.run([
                    model.d_loss,
                    model.g_loss,
                    model.merged
                ], feed_dict={
                    model.x: batch_x,
                    model.c: batch_y,
                    model.z: batch_z
                })

                # print loss
                print("[+] Step %08d => " % (step),
                      "D loss : {:.8f}".format(d_loss), " G loss : {:.8f}".format(g_loss))

                # update overpowered
                d_overpowered = d_loss < g_loss / 3

                # training G model with sample image and noise
                samples = s.run(model.G, feed_dict={
                    model.c: sample_y,
                    model.z: sample_z
                })

                # summary saver
                model.writer.add_summary(summary, step)

                # export image generated by model G
                sample_image_height = model.sample_size
                sample_image_width = model.sample_size
                sample_dir = dirs['sample_output'] + 'train_{:08d}.png'.format(step)

                # Generated image save
                iu.save_images(samples, size=[sample_image_height, sample_image_width],
                               image_path=sample_dir)

                # model save
                model.saver.save(s, dirs['model'], global_step=step)

    end_time = time.time() - start_time

    # elapsed time
    print("[+] Elapsed time {:.8f}s".format(end_time))

    # close tf.Session
    s.close()

if __name__ == '__main__':
    main()
