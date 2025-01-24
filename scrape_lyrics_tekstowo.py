# Makes the current directory the path of the .py file
import os
import sys
os.chdir(sys.path[0])
from bs4 import BeautifulSoup
import requests

def scrape(artist, output_file):

    if artist == "eminem":
        artist_name = 'eminem' # artist_name goes into the url
        number_of_pages = 5 # number_of_pages is taken into account in the for loop to move to the next page
    if artist == 'de la soul':
        artist_name = 'de_la_soul'
        number_of_pages = 2
    if artist == 'biggie':
        artist_name = 'notorious_b_i_g_'
        number_of_pages = 1
    if artist == 'a tribe called quest':
        artist_name = 'a_tribe_called_quest'
        number_of_pages = 1

    # polish artists
    if artist  == "ostr":
        artist_name = 'o_s_t_r_'
        number_of_pages = 4
    if artist == 'paktofonika':
        artist_name = 'paktofonika'
        number_of_pages = 1
    if artist == 'pezet':
        artist_name = 'pezet'
        number_of_pages = 2
    if artist == 'łona i webber':
        artist_name = 'lona_i_webber'
        number_of_pages = 1
    if artist == '52 dębiec':
        artist_name = 'piec_dwa_debiec'
        number_of_pages = 2

    base_url = "https://www.tekstowo.pl"
    with open(output_file, "a", encoding="utf-8") as file: # creating a new file if it doesn't exist, if it does it's just appending the lyrics
        page_number = 1 # starting page number
        for num in range(number_of_pages): # taking into account number_of_pages to move to the next one
            # this is the template url where the name of the artist and the page number are filled in
            url = f"https://www.tekstowo.pl/piosenki_artysty,{artist_name},alfabetycznie,strona,{page_number}.html"
            print(f"page number {page_number} of {artist}")

            # getting the html text of the url
            response = requests.get(url).text # gets the html text as a string
            soup = BeautifulSoup(response, 'html.parser') # parsing the html

            # locatting the song links in the html
            ranking_list = soup.find('div', class_='ranking-lista')
            song_links = ranking_list.select('a.title') # selecting the links in the html

            for link in song_links: # iterating over the links of songs
                song_url = base_url + link['href'] # creating the url
                song_title = link.text.strip() # variable for the title of the song, only to print it, it doesn't go into the output file

                # once in the song page, getting the html   
                song_response = requests.get(song_url)
                song_soup = BeautifulSoup(song_response.text, 'html.parser')
                
                # extracting the lyrics from the appropiate div class
                lyrics_div = song_soup.find('div', class_='inner-text')
                if lyrics_div:
                    lyrics = lyrics_div.get_text().strip() # .strip() revomes html tags
                    file.write(lyrics) # writing to the file only the lyrics, no titles

                    print(f"Saved lyrics for: {song_title}")

            if number_of_pages > 1: # moving to the next page if there is more than 1 page
                page_number += 1
            else:
                break