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
import en_core_web_sm
import pl_core_news_sm

'''
THIS CODE WILL FIRST SCRAPE LYRICS FROM MORE THAN 1500 SONGS AND CREATE TWO .TXT FILES, ONE FOR ENGLISH AND ONE FOR POLISH
AFTERWARDS IT WILL CLEAN THE TEXT OF THE FILE (FIRST ENGLISH, THEN POLISH) OF UNNECESSARY STUFF USING REGEX AND IT WILL TOKENIZE IT USING SPACY 
ONCE ALL OF THAT IS DONE IT WILL CALCULATE ZIPF'S ABBREVIATION LAW AND SHOW A PLOT
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
                    file.write(lyrics) # saving the lyrics to the file

                print(f"Saved lyrics for: {song_title}")

            if number_of_pages > 1: # moving to the next page if there is more than one page
                page_number += 1
            else: # if there is only one page, stop the loop
                break

# list of artists and the name of the file to which append the lyrics
files_and_artists = {'polish_lyrics.txt': ['ostr', 'paktofonika', 'pezet', 'łona i webber', '52 dębiec'], 
                     'english_lyrics.txt': ['eminem', 'de la soul', 'outkast', 'biggie', 'a tribe called quest']}


# double for loop that goes through the list above to scrape said lyrics. It's scraping more than 1500 songs so it takes a couple of minutes
for file, artists in files_and_artists.items():
    for artist in artists:
        scrape(artist, file)

### functions to process text ###

# both functions substitute digits for their text equivalent i.e. 14 for fourteen (in english) or czternaście (in polish)
def digits_to_words_en(match): # extracts the matched digits from the regex (groups them so 14 is fourteen not one four) then runs the function from the library, specifying the language
    
    number = match.group()
    return num2words(number, lang='en')

def digits_to_words_pl(match): # same as the above function
    
    number = match.group()
    return num2words(number, lang='pl')

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

# main function to process the scraped lyrics, need to pass language for the clean_text function primarily but i also use it for more stuff
def process_lyrics(file_path, model, language):

    print(f'\nProcessing {language.capitalize()} lyrics...')

    model.max_length = 3000000 # there are more than 2 million characters so this is needed

    # nlp pipeline starts here
    print('\nCleaning text...')
    doc = model(clean_text(file_path, language))

    # tokenizes and gets the length of each token
    print('\nTokenizing...')
    tokens = [token.text.lower() for token in doc if token.is_alpha] # this is only saving alphabetic characters
    word_lengths = [len(word) for word in tokens]

    print('\nCalculating frequencies...\n')
    # counter gets the frequency of each word length
    length_counts = Counter(word_lengths)

    # sorts by word length (result is a list of tuples, for example: [(1, 533), (2, 324)] ...)
    sorted_length_counts = sorted(length_counts.items())

    # zip(*) unpacks the list of tuples in tuples in two separate variables, i.e. lenghts = (1, 2, 3, 4, 5, 6 ...), frequencies = (312, 233, 167, 53 ...)
    lengths, absolute_frequencies = zip(*sorted_length_counts)

    # calculating relative frequencies (frequency divided by total number of tokens)
    total_tokens = len(tokens)
    print(f'There are {total_tokens} tokens in {file_path}\n')
    relative_frequencies = [freq / total_tokens for freq in absolute_frequencies] # freq in frequencies are already sorted, so no need to do it here

    # filtering lengths up to 20, longer words appear only once in both languages
    lengths = [length for length in lengths if length <= 20]
    absolute_frequencies = [freq for length, freq in zip(lengths, absolute_frequencies) if length <= 20]
    relative_frequencies = [rel_freq for length, rel_freq in zip(lengths, relative_frequencies) if length <= 20]

    # this just prints each length, absolute and relative frequencies
    for length, freq, rel_freq in zip(lengths, absolute_frequencies, relative_frequencies): # need to zip them
        print(f"Length: {length}, Frequency: {freq}, Relative Frequency: {rel_freq:.6f}")

    # code to plot the data
    # simple if statement to choose the colour of the plotted line
    if language == 'polish':
        color = '#E15554'
    else:
        color = '#4D9DE0'

    plt.figure(figsize=(6, 4))
    plt.subplots_adjust(left = 0.155, right=0.935, top=0.910, bottom=0.14)
    plt.plot(lengths, relative_frequencies, marker='o', linestyle='-', color=color)
    plt.xticks(range(1, 19 + 1, 1))
    plt.yticks(np.arange(0, 0.250, 0.025)) # using np.arange to allow for floating point numbers
    plt.xlabel('Word length (in number of characters)')
    plt.ylabel('Relative frequency of word length')
    plt.title(f'Zipf\'s Law of Abbreviation in {language.capitalize()} lyrics')
    # uncomment to save the plot
    # plt.savefig(f'zipf_abbreviation_{language}_relative.pdf', format='pdf')

    plt.show()

### ###

# this is where the models are loaded and where the main functions are called
print('\nLoading models...\n')
nlp_eng = spacy.load('en_core_web_sm') # english model
nlp_pol = spacy.load('pl_core_news_sm') # polish model

# running the main function for english and polish
process_lyrics(file_path='english_lyrics.txt', model=nlp_eng, language='english') # just specifying the arguments for clarity
process_lyrics('polish_lyrics.txt', nlp_pol, 'polish')