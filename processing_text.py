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
import numpy as np

'''
THIS CODE WILL FIRST SCRAPE LYRICS FROM MORE THAN 1500 SONGS AND CREATE TWO .TXT FILES, ONE FOR ENGLISH AND ONE FOR POLISH
AFTERWARDS IT WILL CLEAN THE TEXT OF THE FILE (FIRST ENGLISH, THEN POLISH) OF UNNECESSARY STUFF USING REGEX AND IT WILL TOKENIZE IT USING SPACY 
ONCE ALL OF THAT IS DONE IT WILL CALCULATE ZIPF'S ABBREVIATION LAW AND SHOW A PLOT
IT IS USING AN ENGLISH AND A POLISH SPACY MODEL THAT SHOULD BE DOWNLOADED BEFOREHAND 'en_core_web_sm' and 'pl_core_news_sm'.
'''

### function to scrape ###

def scrape(artist, output_file):

    artist_info = {
        # english artists
        'eminem': ('eminem', 5),
        'de la soul': ('de_la_soul', 2),
        'biggie': ('notorious_b_i_g_', 1),
        'a tribe called quest': ('a_tribe_called_quest', 1),
        'outkast':('outkast', 2),
        
        # polish artists
        'ostr': ('o_s_t_r_', 4),
        'paktofonika': ('paktofonika', 1),
        'pezet': ('pezet', 2),
        'łona i webber': ('lona_i_webber', 1),
        '52 dębiec': ('piec_dwa_debiec', 2)
    }

    # checks if the artist exists in the dictionary above
    if artist in artist_info: # if it does, assign a url name (it goes into the url from which to scrape the lyrics later) and a number of pages that is taken into account in the for loop to move to the next page
        artist_url_name, number_of_pages = artist_info[artist]

    base_url = "https://www.tekstowo.pl" # to create the url of each song

    # creating a new file if it doesn't exist, if it does it's just appending the lyrics
    with open(output_file, "a", encoding="utf-8") as file: 

        page_number = 1 # starting page number

        for num in range(number_of_pages): # taking into account number_of_pages to move to the next one
            # this is the template url where the name of the artist and the page number are filled in
            url = f"https://www.tekstowo.pl/piosenki_artysty,{artist_url_name},alfabetycznie,strona,{page_number}.html"
            print(f"page number {page_number} of {artist}")

            # getting the html text of the url
            response = requests.get(url).text # gets the html text as a string
            soup = BeautifulSoup(response, 'html.parser') # parsing the html

            # locating the song links in the html
            ranking_list = soup.find('div', class_='ranking-lista') # this is finding the list of songs of the artist, there is only one class "ranking_lista"
            song_links = ranking_list.select('a.title') # in the list of songs, select every <a> element with the class "title", it's where the link to the song is located

            for link in song_links: # iterates over the links in the list
                
                song_url = base_url + link['href'] # creates the url. 'href' is the link, it is inside the <a> element previously selected
                song_title = link.text.strip() # variable for the title of the song, this is the text in the <a> element. I only print it, it doesn't go into the output file

                # once in the song site, getting the html. Same thing as the previous code, it is retrieving the html text as a string 
                song_response = requests.get(song_url).text
                song_soup = BeautifulSoup(song_response, 'html.parser')
                
                # extracting the lyrics from the appropiate div class. They are located in a unique class so .find() is enough
                lyrics_div = song_soup.find('div', class_='inner-text')
                if lyrics_div:
                    lyrics = lyrics_div.get_text().strip() # .get_text() revomes html tags, .strip() removes extra whitespaces from the text
                    file.write('\n' + lyrics) # saving the lyrics to the file after a new line

                print(f"Saved lyrics for: {song_title}")

            if number_of_pages > 1: # moving to the next page if there is more than one page
                page_number += 1
            else: # if there is only one page, stop the loop
                break

### functions to process text ###

# both functions substitute digits for their text equivalent i.e. 14 for fourteen (in english) or czternaście (in polish)
def digits_to_words_en(match): # extracts the matched digits from the regex (groups them so 14 is fourteen not one four) then runs the function from the library, specifying the language
    
    number = match.group()
    return num2words(number + ' ', lang='en')

def digits_to_words_pl(match): # same as the above function
    
    number = match.group()
    return num2words(number + ' ', lang='pl')

# function to clean text with regex, it runs inside the process_lyrics function 
# it removes text inside brackets and parenthesis, both included, removes "Chorus" in both languages, 
# substitutes ` for ' and substitutes digits for written numbers
def clean_text(file_path, language):

    with open(file_path, "r", encoding="utf-8") as file:
        cleaned_text = file.read()

    cleaned_text = re.sub(r'[\[\(].*?[\]\)]', '', cleaned_text)  # remove content between brackets and parentheses
    cleaned_text = re.sub(r'\b(Ref\.)|(Refren)|(Chorus)\b', '', cleaned_text) # removes Ref., Refren and Chorus (all mean chorus)
    cleaned_text = re.sub(r'`', "'", cleaned_text) # substitutes ` for ', the second one is the one used in polish and english orthography
    if language == 'polish': # substituting digits for written numbers. This if statement just selects the language (polish or english)
        cleaned_text = re.sub(r'\d+', digits_to_words_pl, cleaned_text)
    else:
        cleaned_text = re.sub(r'\d+', digits_to_words_en, cleaned_text)

    return cleaned_text

# main function to process the scraped lyrics and calculate zipf's law, need to pass language for the clean_text function primarily but i also use it for more stuff
def process_lyrics(file_path, model, language):

    print(f'\nProcessing {language.capitalize()} lyrics...')

    model.max_length = 3000000 # there are more than 2 million characters so this is needed

    # nlp pipeline starts here
    print('\nCleaning text...')
    doc = model(clean_text(file_path, language))

    # tokenizes, gets unique tokens the length of each
    print('\nTokenizing...')
    tokens = [token.text.lower() for token in doc if token.is_alpha] # this is only saving alphabetic characters

    print('\nCalculating frequencies...\n')
    # counter gets the frequency of each token
    length_counts = Counter(tokens)
    
    # filter words with lengths up to 20, since words above that have a frequency of 1
    filtered_length_counts = {word: freq for word, freq in length_counts.items() if len(word) <= 20}

    # calculate word lengths and frequencies for filtered words
    word_lengths = [len(word) for word in filtered_length_counts.keys()]
    word_frequencies = list(filtered_length_counts.values())

    # normalize frequencies to per-million word count
    total_tokens = len(tokens)
    print(f'Total tokens in {language.capitalize()} lyrics: {total_tokens}')
    word_frequencies_per_million = [(freq / total_tokens) * 1_000_000 for freq in word_frequencies]

    # take the logarithm of frequencies for plotting
    log_frequencies = np.log10(word_frequencies_per_million)

    # adds jitter to word lengths and log frequencies in the plot below
    jitter_magnitude = 0.3  # Adjust this value to control the amount of jitter
    jittered_lengths = word_lengths + np.random.uniform(-jitter_magnitude, jitter_magnitude, size=len(word_lengths))
    jittered_frequencies = log_frequencies + np.random.uniform(-jitter_magnitude, jitter_magnitude, size=len(log_frequencies))

    # simple if statement to change the color of the plot below depending on the language
    if language == 'polish':
        color = '#484D6D'
    else:
        color = '#104F55'

    # plot
    plt.figure(figsize=(8, 6))
    plt.subplots_adjust(left=0.155, right=0.935, top=0.910, bottom=0.14)
    plt.scatter(jittered_lengths, jittered_frequencies, alpha=0.5, color=color, s=14)

    # highlight the top 10 most frequent tokens
    number_top_words = 10  # Number of top tokens to highlight
    top_words = sorted(filtered_length_counts.items(), key=lambda word: word[1], reverse=True)[:number_top_words]
    print(f'\nTop tokens in {language.capitalize()}: {top_words}\n')
    
    for word, freq in top_words:
        length = len(word)
        log_freq = np.log10((freq / total_tokens) * 1_000_000) # log of the frequency of the top words
         
        # add jitter to the top words
        jittered_length = length + np.random.uniform(-jitter_magnitude, jitter_magnitude)
        jittered_freq = log_freq + np.random.uniform(-jitter_magnitude, jitter_magnitude)
        plt.scatter(jittered_length, jittered_freq, color= '#EE6352', zorder=2.5, s=18)
        plt.text(jittered_length, jittered_freq, word, fontsize=12, ha='left', va='bottom')

    # Add labels and title
    plt.title(f"Zipf\'s Law of Abbreviation in {language.capitalize()} lyrics")
    plt.xticks(range(1, 20))
    plt.xlabel('Word length (in number of characters)')
    plt.ylabel("Log per-million word count")
    plt.grid(alpha=0.5)
    # plt.savefig(f'zipf_abbreviation_{language}.pdf') # saving the plot

    # Show the plot
    plt.show()

# dictionary of files where the lyrics will be stored and list of artists
files_and_artists = {'polish_lyrics.txt': ['ostr', 'paktofonika', 'pezet', 'łona i webber', '52 dębiec'], 
                     'english_lyrics.txt': ['eminem', 'de la soul', 'outkast', 'biggie', 'a tribe called quest']}

# this is where things happen, the functions are called and the models are loaded
# print('Scraping lyrics...\n')
# # double for loop that goes through the list of files and artists to scrape the lyrics. It's scraping more than 1500 songs so it takes a couple of minutes
# for file, artists in files_and_artists.items():
#     for artist in artists:
#         scrape(artist, file) # scraping function

print('\nLoading models...\n') # loading the models to process the scraped lyrics
nlp_eng = spacy.load('en_core_web_sm') # english model
nlp_pol = spacy.load('pl_core_news_sm') # polish model

# running the main function for english and polish, need to call the file we are reading the content of
process_lyrics(file_path='english_lyrics.txt', model=nlp_eng, language='english') # just specifying the arguments for clarity
process_lyrics('polish_lyrics.txt', nlp_pol, 'polish')