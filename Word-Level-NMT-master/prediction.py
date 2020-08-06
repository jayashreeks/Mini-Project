import pandas as pd
import numpy as np
import string
import pickle
from string import digits
import matplotlib.pyplot as plt
import re
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split
from keras.layers import Input, LSTM, Embedding, Dense
from keras.models import Model
lines= pd.read_table('kan.txt', names=['correct', 'wrong'],delimiter='~')
lines.shape
# Remove quotes
lines.correct=lines.correct.apply(lambda x: re.sub("'", '', x))
lines.wrong=lines.wrong.apply(lambda x: re.sub("'", '', x))
# Remove all numbers from text
#remove_digits = str.maketrans('', '', digits)
lines.correct=lines.correct.apply(lambda x: re.sub("[೦೧೨೩೪೫೬೭೮೯]", "", x))
lines.wrong = lines.wrong.apply(lambda x: re.sub("[೦೧೨೩೪೫೬೭೮೯]", "", x))
# Remove extra spaces
lines.correct=lines.correct.apply(lambda x: x.strip())
lines.wrong=lines.wrong.apply(lambda x: x.strip())
lines.correct=lines.correct.apply(lambda x: re.sub(" +", " ", x))
lines.wrong=lines.wrong.apply(lambda x: re.sub(" +", " ", x))
lines.correct=lines.correct.apply(lambda x: re.sub(r"([?.!,¿])", r" \1 ", x))
lines.wrong=lines.wrong.apply(lambda x: re.sub(r"([?.!,¿])", r" \1 ", x))
# Add start and end tokens to target sequences
lines.correct = lines.correct.apply(lambda x : 'START_ '+ x + ' _END')
# Vocabulary of English
all_correct_words=set()
for correct in lines.correct:
    for word in correct.split():
        if word not in all_correct_words:
            all_correct_words.add(word)

# Vocabulary of French 
all_wrong_words=set()
for wrong in lines.wrong:
    for word in wrong.split():
        if word not in all_wrong_words:
            all_wrong_words.add(word)
# Max Length of source sequence
lenght_list=[]
for l in lines.wrong:
    lenght_list.append(len(l.split(' ')))
max_length_src = np.max(lenght_list)
# Max Length of target sequence
lenght_list=[]
for l in lines.correct:
    lenght_list.append(len(l.split(' ')))
max_length_tar = np.max(lenght_list)
input_words = sorted(list(all_wrong_words))
target_words = sorted(list(all_correct_words))
num_encoder_tokens = len(all_wrong_words)
num_decoder_tokens = len(all_correct_words)
num_encoder_tokens+=1
num_decoder_tokens += 1 # For zero padding
input_token_index = dict([(word, i+1) for i, word in enumerate(input_words)])
target_token_index = dict([(word, i+1) for i, word in enumerate(target_words)])
reverse_input_char_index = dict((i, word) for word, i in input_token_index.items())
reverse_target_char_index = dict((i, word) for word, i in target_token_index.items())
lines = shuffle(lines)
# Train - Test Split
X, y = lines.wrong, lines.correct
with open('Weights/X_train.pkl', 'rb') as f:
    X_train = pickle.load(f)
with open('Weights/X_test.pkl', 'rb') as f:
    X_test = pickle.load(f)
with open('Weights/y_train.pkl', 'rb') as f:
    y_train = pickle.load(f)
with open('Weights/y_test.pkl', 'rb') as f:
    y_test = pickle.load(f)
def generate_batch(X = X_train, y = y_train, batch_size = 32):
    ''' Generate a batch of data '''
    while True:
        for j in range(0, len(X), batch_size):
            encoder_input_data = np.zeros((batch_size, max_length_src),dtype='float32')
            decoder_input_data = np.zeros((batch_size, max_length_tar),dtype='float32')
            decoder_target_data = np.zeros((batch_size, max_length_tar, num_decoder_tokens),dtype='float32')
            for i, (input_text, target_text) in enumerate(zip(X[j:j+batch_size], y[j:j+batch_size])):
                for t, word in enumerate(input_text.split()):
                    encoder_input_data[i, t] = input_token_index[word] # encoder input seq
                for t, word in enumerate(target_text.split()):
                    if t<len(target_text.split())-1:
                        decoder_input_data[i, t] = target_token_index[word] # decoder input seq
                    if t>0:
                        # decoder target sequence (one hot encoded)
                        # does not include the START_ token
                        # Offset by one timestep
                        decoder_target_data[i, t - 1, target_token_index[word]] = 1.
            yield([encoder_input_data, decoder_input_data], decoder_target_data)
            
latent_dim = 50
# Encoder
encoder_inputs = Input(shape=(None,))
enc_emb =  Embedding(num_encoder_tokens, latent_dim, mask_zero = True)(encoder_inputs)
encoder_lstm = LSTM(latent_dim, return_state=True)
encoder_outputs, state_h, state_c = encoder_lstm(enc_emb)
# We discard `encoder_outputs` and only keep the states.
encoder_states = [state_h, state_c]

# Set up the decoder, using `encoder_states` as initial state.
decoder_inputs = Input(shape=(None,))
dec_emb_layer = Embedding(num_decoder_tokens, latent_dim, mask_zero = True)
dec_emb = dec_emb_layer(decoder_inputs)
# We set up our decoder to return full output sequences,
# and to return internal states as well. We don't use the
# return states in the training model, but we will use them in inference.
decoder_lstm = LSTM(latent_dim, return_sequences=True, return_state=True)
decoder_outputs, _, _ = decoder_lstm(dec_emb,
                                     initial_state=encoder_states)
decoder_dense = Dense(num_decoder_tokens, activation='softmax')
decoder_outputs = decoder_dense(decoder_outputs)

# Define the model that will turn
# `encoder_input_data` & `decoder_input_data` into `decoder_target_data`
model = Model([encoder_inputs, decoder_inputs], decoder_outputs)

model.compile(optimizer='rmsprop', loss='categorical_crossentropy', metrics=['acc'])


train_samples = len(X_train)
val_samples = len(X_test)
batch_size = 32
epochs = 100

# Encode the input sequence to get the "thought vectors"
encoder_model = Model(encoder_inputs, encoder_states)

# Decoder setup
# Below tensors will hold the states of the previous time step
decoder_state_input_h = Input(shape=(latent_dim,))
decoder_state_input_c = Input(shape=(latent_dim,))
decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]

dec_emb2= dec_emb_layer(decoder_inputs) # Get the embeddings of the decoder sequence

# To predict the next word in the sequence, set the initial states to the states from the previous time step
decoder_outputs2, state_h2, state_c2 = decoder_lstm(dec_emb2, initial_state=decoder_states_inputs)
decoder_states2 = [state_h2, state_c2]
decoder_outputs2 = decoder_dense(decoder_outputs2) # A dense softmax layer to generate prob dist. over the target vocabulary

# Final decoder model
decoder_model = Model(
    [decoder_inputs] + decoder_states_inputs,
    [decoder_outputs2] + decoder_states2)

def decode_sequence(input_seq):
    # Encode the input as state vectors.
    states_value = encoder_model.predict(input_seq)
    # Generate empty target sequence of length 1.
    target_seq = np.zeros((1,1))
    # Populate the first character of target sequence with the start character.
    target_seq[0, 0] = target_token_index['START_']
    # Sampling loop for a batch of sequences
    # (to simplify, here we assume a batch of size 1).
    stop_condition = False
    decoded_sentence = ''
    while not stop_condition:
        output_tokens, h, c = decoder_model.predict([target_seq] + states_value)
        # Sample a token
        sampled_token_index = np.argmax(output_tokens[0, -1, :])
        sampled_char = reverse_target_char_index[sampled_token_index]
        decoded_sentence += ' '+sampled_char
        # Exit condition: either hit max length
        # or find stop character.
        if (sampled_char == '_END' or
           len(decoded_sentence) > 50):
            stop_condition = True
        # Update the target sequence (of length 1).
        target_seq = np.zeros((1,1))
        target_seq[0, 0] = sampled_token_index
        # Update states
        states_value = [h, c]
    return decoded_sentence

model.load_weights('kannadamodel_weights.h5')
'''
text='ಅವರು ಅಳುತ್ತಿದ್ದಾನೆ '
input_seq=np.zeros([1,12],dtype='float32')
j=0
for word in text.split():
    input_seq[0][j]=(input_token_index[word])
    j=j+1
decode_sentence=decode_sequence(input_seq)
print(decode_sentence[:-4])
'''