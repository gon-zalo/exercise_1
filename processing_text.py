import spacy
from collections import Counter
from scrape_lyrics_tekstowo import scrape # importing my scraping file
import en_core_web_sm
import pl_core_news_sm
import matplotlib.pyplot as plt

# scrapes all the lyrics and saves them to a .txt
# scrape('ostr', 'polish_lyrics.txt')
# scrape('paktofonika', 'polish_lyrics.txt')
# scrape('pezet', 'polish_lyrics.txt')
# scrape('łona i webber', 'polish_lyrics.txt')
# scrape('52 dębiec', 'polish_lyrics.txt')
# scrape('eminem', 'english_lyrics.txt')
# scrape('de la soul', 'english_lyrics.txt')
# scrape('biggie', 'english_lyrics.txt')
# scrape('a tribe called quest', 'english_lyrics.txt')

file_polish = 'polish_lyrics_small.txt'
# file_english = 'english_lyrics_small.txt'

with open(file_polish, "r", encoding="utf-8") as file:
    text_pol = file.read()

# with open(file_english, "r", encoding="utf-8") as file:
#     text_eng = file.read()

# nlp_eng = en_core_web_sm.load()
nlp_pol = spacy.load('pl_core_news_sm')

nlp_pol.max_length = 2000000

doc_pol = nlp_pol(text_pol)

tokens_pol = [token.text.lower() for token in doc_pol if token.is_alpha]
# lemmas_pol = [token.lemma_ for token in doc_pol]

# getting the length of each token
word_lengths_pol = [len(word) for word in tokens_pol]

# Use Counter to get the frequency of each word length
length_counts = Counter(word_lengths_pol)

# Sort by word length (result is a list of tuples, for example: [(1, 533), (2, 324)] ...)
sorted_length_counts = sorted(length_counts.items())

# zip(*) unpacks the list of tuples in tuples in two separate variables, i.e. lenghts = (1, 2, 3, 4, 5, 6)
lengths, frequencies = zip(*sorted_length_counts)

for length, freq in sorted_length_counts:
    print(f"Length: {length}, Frequency: {freq}")

# # # Plot the graph (Zipf's Law of Abbreviation)
plt.figure(figsize=(10, 6))
plt.plot(lengths, frequencies, marker='o', linestyle='-', color='#5B5F97')
plt.xticks(range(0, 30 + 1, 1))  # Adjust the step (2 in this case) for more ticks
plt.xlabel('Word Length (in number of characters)')
plt.ylabel('Frequency of Word Length (absolute values)')
plt.title('Zipf\'s Law of Abbreviation in Polish')
plt.show()