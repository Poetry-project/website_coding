import tensorflow as tf
import json
import os
from tensorflow.keras.layers.experimental import preprocessing

class MyModel(tf.keras.Model):
  def __init__(self, vocab_size, embedding_dim, rnn_units):
    super().__init__(self)
    self.embedding = tf.keras.layers.Embedding(vocab_size, embedding_dim)
    self.gru = tf.keras.layers.GRU(rnn_units,
                                   return_sequences=True,
                                   return_state=True)
    self.dense = tf.keras.layers.Dense(vocab_size)

  def call(self, inputs, states=None, return_state=False, training=False):
    x = inputs
    x = self.embedding(x, training=training)
    if states is None:
      states = self.gru.get_initial_state(x)
    x, states = self.gru(x, initial_state=states, training=training)
    x = self.dense(x, training=training)

    if return_state:
      return x, states
    else:
      return x

class OneStep(tf.keras.Model):
  def __init__(self, model, chars_from_ids, ids_from_chars, temperature=1.0):
    super().__init__()
    self.temperature = temperature
    self.model = model
    self.chars_from_ids = chars_from_ids
    self.ids_from_chars = ids_from_chars

    # Create a mask to prevent "[UNK]" from being generated.
    skip_ids = self.ids_from_chars(['[UNK]'])[:, None]
    sparse_mask = tf.SparseTensor(
        # Put a -inf at each bad index.
        values=[-float('inf')]*len(skip_ids),
        indices=skip_ids,
        # Match the shape to the vocabulary
        dense_shape=[len(ids_from_chars.get_vocabulary())])
    self.prediction_mask = tf.sparse.to_dense(sparse_mask)

  @tf.function
  def generate_one_step(self, inputs, states=None):
    # Convert strings to token IDs.
    input_chars = tf.strings.unicode_split(inputs, 'UTF-8')
    input_ids = self.ids_from_chars(input_chars).to_tensor()

    # Run the model.
    # predicted_logits.shape is [batch, char, next_char_logits]
    predicted_logits, states = self.model(inputs=input_ids, states=states,
                                          return_state=True)
    # Only use the last prediction.
    predicted_logits = predicted_logits[:, -1, :]
    predicted_logits = predicted_logits/self.temperature
    # Apply the prediction mask: prevent "[UNK]" from being generated.
    predicted_logits = predicted_logits + self.prediction_mask

    # Sample the output logits to generate token IDs.
    predicted_ids = tf.random.categorical(predicted_logits, num_samples=1)
    predicted_ids = tf.squeeze(predicted_ids, axis=-1)

    # Convert from token ids to characters
    predicted_chars = self.chars_from_ids(predicted_ids)

    # Return the characters and model state.
    return predicted_chars, states

class GenerateText():
  def __init__(self) :

    self.save_dir = "output/"
    with open(os.path.join(self.save_dir, "config.json"), "r") as config_file:
      config = json.load(config_file)

    # String Lookup layer, which assign to every char an id
    self.ids_from_chars = preprocessing.StringLookup(vocabulary=config['vocab'], mask_token=None)
    # String lookup layer with invert = true, so from id it return to char given the vocabulary
    self.chars_from_ids = tf.keras.layers.experimental.preprocessing.StringLookup(
        vocabulary=self.ids_from_chars.get_vocabulary(), invert=True, mask_token=None)

    # self.seq_length = 100
    self.seq_length = config['seq_length']
    # Build The Model
    # Length of the vocabulary in StringLookup Layer
    self.vocab_size = len(self.ids_from_chars.get_vocabulary())

    # The embedding dimension
    # self.embedding_dim = 256
    self.embedding_dim = config['embedding_dim']

    # Number of RNN units
    # self.rnn_units = 1024
    self.rnn_units = config['rnn_units']

    self. model = MyModel( vocab_size=self.vocab_size, 
                            embedding_dim= self.embedding_dim,
                            rnn_units=self.rnn_units)

    self.one_step_model = OneStep(self.model, self.chars_from_ids, self.ids_from_chars)
    self.one_step_reloaded =  tf.saved_model.load( os.path.join(self.save_dir, "one_step"))
    # url = 'https://drive.google.com/drive/folders/11hv60qPQGzltGzw0ZuphdQ0QOqP_Wy7Z?usp=drive_link'    
    # self.one_step_reloaded = tf.saved_model.load(url)


  def predict (self , seed_text,  seq_length=100):
      states = None
      next_char = tf.constant([seed_text])
      result = [next_char]

      for n in range(seq_length):
        next_char, states = self.one_step_reloaded.generate_one_step(next_char, states=states)
        result.append(next_char)

      # print(tf.strings.join(result)[0].numpy().decode("utf-8"))      
      return tf.strings.join(result)[0].numpy().decode("utf-8")