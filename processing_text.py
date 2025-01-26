# Makes the current directory the path of the .py file
import os
import sys
os.chdir(sys.path[0])

# libraries needed
import spacy
from bs4 import BeautifulSoup
import requests
import matplotlib.pyplot as plt
from collections import Counter
import re
from num2words import num2words
import en_core_web_sm
import pl_core_news_sm


# scraping function to get the song lyrics
def scrape(artist, output_file):

    artist_info = {
        # english artists
        'eminem': ('eminem', 5),
        'de la soul': ('de_la_soul', 2),
        'biggie': ('notorious_b_i_g_', 1),
        'a tribe called quest': ('a_tribe_called_quest', 1),
        
        # polish artists
        'ostr': ('o_s_t_r_', 4),
        'paktofonika': ('paktofonika', 1),
        'pezet': ('pezet', 2),
        'łona i webber': ('lona_i_webber', 1),
        '52 dębiec': ('piec_dwa_debiec', 2)
    }

    # checks if the artist exists in the dictionary above
    if artist in artist_info: # if it does, assign a name (that goes into the url from which to scrape the lyrics later) and a number of pages that is taken into account in the for loop to move to the next page
        artist_name, number_of_pages = artist_info[artist]

    base_url = "https://www.tekstowo.pl" # to create the url of each song
    # creating a new file if it doesn't exist, if it does it's just appending the lyrics
    with open(output_file, "a", encoding="utf-8") as file: 
        page_number = 1 # starting page number
        for num in range(number_of_pages): # taking into account number_of_pages to move to the next one
            # this is the template url where the name of the artist and the page number are filled in
            url = f"https://www.tekstowo.pl/piosenki_artysty,{artist_name},alfabetycznie,strona,{page_number}.html"
            print(f"page number {page_number} of {artist}")

            # getting the html text of the url
            response = requests.get(url).text # gets the html text as a string
            soup = BeautifulSoup(response, 'html.parser') # parsing the html

            # locating the song links in the html
            ranking_list = soup.find('div', class_='ranking-lista') # this is finding the list of songs of the artist, there is only one class "ranking_lista"
            song_links = ranking_list.select('a.title') # in the list of songs, select every <a> element with the class "title", it's where the link to the song is located

            for link in song_links: # iterates over the links
                song_url = base_url + link['href'] # creates the url. 'href' is the link, it is inside the <a> element previously selected
                song_title = link.text.strip() # variable for the title of the song, this is also in the <a> element. I only print it, it doesn't go into the output file

                # once in the song page, getting the html. Same as the previous code 
                song_response = requests.get(song_url).text
                song_soup = BeautifulSoup(song_response, 'html.parser')
                
                # extracting the lyrics from the appropiate div class. There is only one class so .find() is enough
                lyrics_div = song_soup.find('div', class_='inner-text')
                lyrics = lyrics_div.get_text().strip() # .get_text() revomes html tags, .strip() removes extra whitespaces from the text
                file.write(lyrics) # writing the lyrics to the file, no titles

                print(f"Saved lyrics for: {song_title}")

            if number_of_pages > 1: # moving to the next page if there is more than one page
                page_number += 1
            else: # if there is only one page, stop the loop
                break

# list of artists and the name of the file to which append the lyrics
artists_and_files = [
    ('ostr', 'polish_lyrics.txt'),
    ('paktofonika', 'polish_lyrics.txt'),
    ('pezet', 'polish_lyrics.txt'),
    ('łona i webber', 'polish_lyrics.txt'),
    ('52 dębiec', 'polish_lyrics.txt'),
    ('eminem', 'english_lyrics.txt'),
    ('de la soul', 'english_lyrics.txt'),
    ('biggie', 'english_lyrics.txt'),
    ('a tribe called quest', 'english_lyrics.txt'),
]

# for loop that goes through the list above to scrape said lyrics. It's scraping more than 1400 songs so it takes a couple of minutes.
# for artist, file in artists_and_files:
#     scrape(artist, file)

### FUNCTIONS ###
# both functions substitute digits for their text equivalent i.e. 14 for fourteen
def digits_to_words_pl(match):
    # Extract the matched digits from the regex
    number = match.group()

    # Convert the number to words in Polish
    return num2words(number, lang='pl')

def digits_to_words_en(match):

    number = match.group()
    return num2words(number, lang='en')

# function to clean text with regex, it runs inside the process_lyrics function 
# it removes text inside brackets and parenthesis, both included, removes "Chorus" in both languages, 
# substitutes ` for ' and substitutes digits for numbers in text
def clean_text(file_path, language):

    with open(file_path, "r", encoding="utf-8") as file:
        cleaned_text = file.read()

    cleaned_text = re.sub(r'[\[\(].*?[\]\)]', '', cleaned_text)  # remove content between brackets and parentheses
    cleaned_text = re.sub(r'\b(Ref\.)|(Refren)|(Chorus)\b', '', cleaned_text) # removes Ref., Refren and Chorus (all mean chorus)
    cleaned_text = re.sub(r'`', "'", cleaned_text) # substitutes ` for ', the second one is the one used in polish and english orthography
    if language == 'polish': # substituting digits for numbers in text. This if statement just selects the language (polish or english)
        cleaned_text = re.sub(r'\d+', digits_to_words_pl, cleaned_text)
    else:
        cleaned_text = re.sub(r'\d+', digits_to_words_en, cleaned_text)

    return cleaned_text

# function to process the scraped lyrics
def process_lyrics(file_path, model, language):

    print(f'\nProcessing {language} lyrics...')
    # this is just for the name of the plot
    if language == 'polish':
        model_name = 'Polish'
    else:
        model_name = 'English'

    model.max_length = 3000000 # there are more than 2 million characters so this is needed

    # nlp pipeline starts here
    print('\nCleaning text...')
    doc = model(clean_text(file_path, language))

    # tokenizes and gets the length of each token
    print('\nTokenizing...')
    tokens = [token.text.lower() for token in doc if token.is_alpha]
    word_lengths = [len(word) for word in tokens]

    print('\nCalculating frequencies...\n')
    # Counter gets the frequency of each word length
    length_counts = Counter(word_lengths)

    # sorts by word length (result is a list of tuples, for example: [(1, 533), (2, 324)] ...)
    sorted_length_counts = sorted(length_counts.items())

    # zip(*) unpacks the list of tuples in tuples in two separate variables, i.e. lenghts = (1, 2, 3, 4, 5, 6 ...), frequencies = (312, 233, 167, 53 ...)
    lengths, absolute_frequencies = zip(*sorted_length_counts)

    # calculating relative frequencies (frequency divided by total number of tokens)
    total_tokens = len(tokens)
    relative_frequencies = [freq / total_tokens for freq in absolute_frequencies] # freq in frequencies are already sorted, so no need to do it here

    # filtering lengths up to 20, longer words appear only once in both languages
    lengths = [length for length in lengths if length <= 20]
    absolute_frequencies = [freq for length, freq in zip(lengths, absolute_frequencies) if length <= 20]
    relative_frequencies = [rel_freq for length, rel_freq in zip(lengths, relative_frequencies) if length <= 20]

    # this just prints each length, absolute and relative frequencies
    for length, freq, rel_freq in zip(lengths, absolute_frequencies, relative_frequencies): # need to zip them
        print(f"Length: {length}, Frequency: {freq}, Relative Frequency: {rel_freq:.6f}")

    # this code plots two graphs, one with absolute frequencies and another with relative frequencies
    plt.figure(figsize=(10, 6))
    plt.plot(lengths, absolute_frequencies, marker='o', linestyle='-', color='#DF9B6D')
    plt.xticks(range(1, 19 + 1, 1))
    plt.xlabel('Word Length (in number of characters)')
    plt.ylabel('Absolute frequency of word length')
    plt.title(f'Zipf\'s Law of Abbreviation in {model_name} lyrics')
    plt.savefig(f'zipf_abbreviation_{language}_absolute.png')

    plt.figure(figsize=(10, 6))
    plt.plot(lengths, relative_frequencies, marker='o', linestyle='-', color='#473144')
    plt.xticks(range(1, 19 + 1, 1))
    plt.xlabel('Word Length (in number of characters)')
    plt.ylabel('Relative frequency of word length')
    plt.title(f'Zipf\'s Law of Abbreviation in {model_name} lyrics')
    plt.savefig(f'zipf_abbreviation_{language}_relative.png')

    plt.show()

### ###

# loading the models
print('\nLoading models...\n')
nlp_pol = spacy.load('pl_core_news_sm')
nlp_eng = spacy.load('en_core_web_sm')

process_lyrics(file_path='polish_lyrics.txt', model=nlp_pol, language='polish')
process_lyrics('english_lyrics.txt', nlp_eng, 'english')