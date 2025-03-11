# -*- coding: utf-8 -*-

'''
    Mozikatalogus Addon
    Copyright (C) 2023 heg, vargalex

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os, sys, re, xbmc, xbmcgui, xbmcplugin, xbmcaddon, locale, base64
from bs4 import BeautifulSoup
import requests
import urllib.parse
import resolveurl as urlresolver
from resources.lib.modules.utils import py2_decode, py2_encode
import html
import re, json

from urllib.parse import urljoin, urlparse, parse_qs
from resources.lib.modules import xmltodict
import struct
import random
import string

sysaddon = sys.argv[0]
syshandle = int(sys.argv[1])
addonFanart = xbmcaddon.Addon().getAddonInfo('fanart')

version = xbmcaddon.Addon().getAddonInfo('version')
kodi_version = xbmc.getInfoLabel('System.BuildVersion')
base_log_info = f'Mozikatalogus | v{version} | Kodi: {kodi_version[:5]}'

xbmc.log(f'{base_log_info}', xbmc.LOGINFO)

base_url = 'https://mozikatalogus.hu'

headers = {
    'authority': 'mozikatalogus.hu',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
}

if sys.version_info[0] == 3:
    from xbmcvfs import translatePath
    from urllib.parse import urlparse, quote_plus
else:
    from xbmc import translatePath
    from urlparse import urlparse
    from urllib import quote_plus

class navigator:
    def __init__(self):
        try:
            locale.setlocale(locale.LC_ALL, "hu_HU.UTF-8")
        except:
            try:
                locale.setlocale(locale.LC_ALL, "")
            except:
                pass
        self.base_path = py2_decode(translatePath(xbmcaddon.Addon().getAddonInfo('profile')))
        self.searchFileName = os.path.join(self.base_path, "search.history")

    def root(self):
        self.addDirectoryItem("Filmek", "only_movies", '', 'DefaultFolder.png')
        self.addDirectoryItem("Sorozatok", "only_series", '', 'DefaultFolder.png')
        self.addDirectoryItem("Kategóriák", "categories", '', 'DefaultFolder.png')
        self.addDirectoryItem("Színészek", f"actor_items&url={base_url}/szineszek", '', 'DefaultFolder.png')
        self.addDirectoryItem("Keresés (Színészek)", "actor_search", '', 'DefaultFolder.png')
        self.addDirectoryItem("Keresés", "search", '', 'DefaultFolder.png')
        self.endDirectory()
        
    def getCategories(self):
        static_data = [
            {"category_link": "https://mozikatalogus.hu/filmek-es-sorozatok/2024-2025", "category_title": "Megjelent 2024-2025"},
            {"category_link": "https://mozikatalogus.hu/legjobbra-ertekelt-filmek-es-sorozatok", "category_title": "Legjobbra értékelt"},
            {"category_link": "https://mozikatalogus.hu/legujabb-filmek-es-sorozatok", "category_title": "Legfrissebb"},
            {"category_link": "https://mozikatalogus.hu/zs-filmek-es-sorozatok", "category_title": "Zs Filmek"},
            {"category_link": "https://mozikatalogus.hu/kategoria/disney", "category_title": "Disney"},
            {"category_link": "https://mozikatalogus.hu/kategoria/netflix", "category_title": "Netflix"},
            {"category_link": "https://mozikatalogus.hu/kategoria/minisorozat", "category_title": "Minisorozat"},
            {"category_link": "https://mozikatalogus.hu/kategoria/karacsony", "category_title": "Karácsony"},
            {"category_link": "https://mozikatalogus.hu/kategoria/akcio", "category_title": "Akció"},
            {"category_link": "https://mozikatalogus.hu/kategoria/animacios", "category_title": "Animációs"},
            {"category_link": "https://mozikatalogus.hu/kategoria/anime", "category_title": "Anime"},
            {"category_link": "https://mozikatalogus.hu/kategoria/azsiai", "category_title": "Ázsiai"},
            {"category_link": "https://mozikatalogus.hu/kategoria/dokumentum", "category_title": "Dokumentum"},
            {"category_link": "https://mozikatalogus.hu/kategoria/drama", "category_title": "Dráma"},
            {"category_link": "https://mozikatalogus.hu/kategoria/fantasy", "category_title": "Fantasy"},
            {"category_link": "https://mozikatalogus.hu/kategoria/haborus", "category_title": "Háborús"},
            {"category_link": "https://mozikatalogus.hu/kategoria/halloween", "category_title": "Halloween"},
            {"category_link": "https://mozikatalogus.hu/kategoria/horror", "category_title": "Horror"},
            {"category_link": "https://mozikatalogus.hu/kategoria/kaland", "category_title": "Kaland"},
            {"category_link": "https://mozikatalogus.hu/kategoria/katasztrofa", "category_title": "Katasztrófa"},
            {"category_link": "https://mozikatalogus.hu/kategoria/krimi", "category_title": "Krimi"},
            {"category_link": "https://mozikatalogus.hu/kategoria/misztikus", "category_title": "Misztikus"},
            {"category_link": "https://mozikatalogus.hu/kategoria/pszicho", "category_title": "Pszicho"},
            {"category_link": "https://mozikatalogus.hu/kategoria/regi-magyar", "category_title": "Régi magyar"},
            {"category_link": "https://mozikatalogus.hu/kategoria/romantikus", "category_title": "Romantikus"},
            {"category_link": "https://mozikatalogus.hu/kategoria/sci-fi", "category_title": "Sci-fi"},
            {"category_link": "https://mozikatalogus.hu/kategoria/telenovella", "category_title": "Telenovella"},
            {"category_link": "https://mozikatalogus.hu/kategoria/thriller", "category_title": "Thriller"},
            {"category_link": "https://mozikatalogus.hu/kategoria/vigjatek", "category_title": "Vígjáték"},
            {"category_link": "https://mozikatalogus.hu/kategoria/western", "category_title": "Western"},
        ]

        page = requests.get(f"{base_url}", headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')
        
        categories = soup.find_all('a', class_='label')
        
        for category in categories:
            category_link = category['href']
        
            category_name_div = category.find('div', class_='category-name')
            category_title = category_name_div.text.strip().replace('\n', '') if category_name_div else None
        
            category_count_div = category.find('div', class_='category-count')
            category_count = category_count_div.text.strip() if category_count_div else None

            if category_title is not None:
                data_item = {"category_link": category_link, "category_title": category_title}

                if category_count is not None:
                    data_item["category_count"] = category_count

                static_data.append(data_item)

        for data_item in static_data:
            category_link = data_item["category_link"]
            category_title = data_item["category_title"]

            category_count = data_item.get("category_count", None)

            if category_count is not None:
                self.addDirectoryItem(f"{category_title} - ({category_count})", f'items&url={quote_plus(category_link)}', '', 'DefaultFolder.png')
            else:
                self.addDirectoryItem(f"{category_title}", f'items&url={quote_plus(category_link)}', '', 'DefaultFolder.png')
        
        self.endDirectory('movies')

    def getItems(self, url):
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')
        
        custom_tags = ['film-card-component','film-card-big-component']
        content_list = []
        for tag in soup.find_all(custom_tags):
            film_json = tag.get(':film')
            if film_json:
                film_json_clean = html.unescape(film_json)
                try:
                    parsed_film = json.loads(film_json_clean)
                    if parsed_film.get('type') == 1:
                        parsed_film['main_type'] = 'Film'
                    elif parsed_film.get('type') == 2:
                        parsed_film['main_type'] = 'Sorozat'
                    if parsed_film.get('language') == 'hu':
                        parsed_film['lang_type'] = 'Szinkronos'
                    else:
                        parsed_film['lang_type'] = 'Feliratos'
                    content_list.append(parsed_film)
                except json.JSONDecodeError as e:
                    print(f"Error decoding film JSON: {e}")     
  
        for stuffs in content_list:
            slug_part = stuffs['slug']
            
            hun_title = stuffs['hungarian_title']
            lang_type = stuffs['lang_type']
            
            img_part = stuffs['img']
            img_url = f'{base_url}{img_part}'
            
            content = stuffs['description']
            
            main_type = stuffs['main_type']
            
            if main_type == 'Film':
                
                main_type = f'{main_type:^10}'
                
                link_url = stuffs['url']
                
                if lang_type == 'Feliratos':
                    lang_type = f' - ([COLOR red]Feliratos[/COLOR])'
                
                    self.addDirectoryItem(f'[B]|{main_type}| {hun_title}{lang_type}[/B]', f'playmovie&url={quote_plus(link_url)}&img_url={img_url}&hun_title={hun_title}&content={content}', img_url, 'DefaultMovies.png', isFolder=False, meta={'title': hun_title, 'plot': content})
                else:    
                    self.addDirectoryItem(f'[B]|{main_type}| {hun_title}[/B]', f'playmovie&url={quote_plus(link_url)}&img_url={img_url}&hun_title={hun_title}&content={content}', img_url, 'DefaultMovies.png', isFolder=False, meta={'title': hun_title, 'plot': content})
            else:
                
                link_url = f'{base_url}/film/{slug_part}'
                if lang_type == 'Feliratos':
                    lang_type = f' - ([COLOR red]Feliratos[/COLOR])'
                
                    self.addDirectoryItem(f'[B]|{main_type}| {hun_title}{lang_type}[/B]', f'extract_series&url={quote_plus(link_url)}&img_url={img_url}&hun_title={hun_title}&content={content}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})
                else:    
                    self.addDirectoryItem(f'[B]|{main_type}| {hun_title}[/B]', f'extract_series&url={quote_plus(link_url)}&img_url={img_url}&hun_title={hun_title}&content={content}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})
        
        try:
            pagination = soup.find('div', class_='flex-fill paginate mb-3')
            if pagination:
                next_page_link = pagination.find('a', {'aria-label': 'Next »'})
                if next_page_link:
                    next_page_url = next_page_link.get('href')
                    self.addDirectoryItem('[I]Következő oldal[/I]', f'items&url={quote_plus(next_page_url)}', '', 'DefaultFolder.png')
        except Exception as e:
            xbmc.log(f'{base_log_info}| getOnlyMovies | next_page_url | csak egy oldal található - {e}', xbmc.LOGINFO)
        
        self.endDirectory('movies')

    def getActorItems(self, url):
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')

        actor_cards = soup.find_all("a", class_="actor-card")
        for card in actor_cards:
            actor_link = card.get("href")

            inner_div = card.find("div", class_="actor-card")
            style_attr = inner_div.get("style", "")
            img_match = re.search(r"url\('([^']+)'\)", style_attr)
            actor_img_url = img_match.group(1) if img_match else None

            actor_name = card.find("h2").get_text(strip=True)

            film_info = card.find("div", class_="content").get_text(strip=True)
            film_count_match = re.search(r'\((\d+)\)', film_info)
            film_count = int(film_count_match.group(1)) if film_count_match else 0
            
            self.addDirectoryItem(f'[B]{actor_name} - ({film_count})[/B]', f'items&url={quote_plus(actor_link)}', actor_img_url, 'DefaultMovies.png', isFolder=True, meta={'title': actor_name})
        
        try:
            pagination = soup.find("ul", class_="pagination")
            if pagination:
                next_page_tag = pagination.find("a", rel="next")
                if next_page_tag:
                    next_page_link = next_page_tag.get("href")
                    raw_page_match = re.search(r'page=(\d+)', next_page_link)
                    if raw_page_match:
                        raw_page_num = raw_page_match.group(1)
                        if re.search(r'search', url):
                            next_page_url = f'{url}&page={raw_page_num}'
                        else:
                            next_page_url = f'{next_page_link}'
                        self.addDirectoryItem('[I]Következő oldal[/I]', f'actor_items&url={quote_plus(next_page_url)}', '', 'DefaultFolder.png')
        except Exception as e:
            xbmc.log(f'{base_log_info}| getOnlyMovies | next_page_url | csak egy oldal található - {e}', xbmc.LOGINFO)
        
        self.endDirectory('movies')
    
    def getOnlyMovies(self):
        page = requests.get(f"{base_url}/filmek", headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')
        
        custom_tags = ['film-card-component','film-card-big-component']
        content_list = []
        for tag in soup.find_all(custom_tags):
            film_json = tag.get(':film')
            if film_json:
                film_json_clean = html.unescape(film_json)
                try:
                    parsed_film = json.loads(film_json_clean)
                    if parsed_film.get('type') == 1:
                        parsed_film['main_type'] = 'Film'
                    elif parsed_film.get('type') == 2:
                        parsed_film['main_type'] = 'Sorozat'
                    if parsed_film.get('language') == 'hu':
                        parsed_film['lang_type'] = 'Szinkronos'
                    else:
                        parsed_film['lang_type'] = 'Feliratos'
                    content_list.append(parsed_film)
                except json.JSONDecodeError as e:
                    print(f"Error decoding film JSON: {e}")
            
        for stuffs in content_list:
            slug_part = stuffs['slug']
            
            link_url = stuffs['url']
            
            hun_title = stuffs['hungarian_title']
            lang_type = stuffs['lang_type']
            
            img_part = stuffs['img']
            img_url = f'{base_url}{img_part}'
            
            content = stuffs['description']

            if lang_type == 'Feliratos':
                display_title = f'[B]{hun_title} - ([COLOR red]feliratos[/COLOR])[/B]'
            else:
                display_title = f'[B]{hun_title}[/B]'
            
            url_part = f'playmovie&url={quote_plus(link_url)}&img_url={img_url}&hun_title={quote_plus(hun_title)}&content={content}'
            self.addDirectoryItem(display_title, url_part, img_url, 'DefaultMovies.png', isFolder=False, meta={'title': hun_title, 'plot': content})
        
        try:
            pagination = soup.find('div', class_='flex-fill paginate mb-3')
            if pagination:
                next_page_link = pagination.find('a', {'aria-label': 'Next »'})
                if next_page_link:
                    next_page_url = next_page_link.get('href')
                    self.addDirectoryItem('[I]Következő oldal[/I]', f'movie_items&url={quote_plus(next_page_url)}', '', 'DefaultFolder.png')
        except Exception as e:
            xbmc.log(f'{base_log_info}| getOnlyMovies | next_page_url | csak egy oldal található - {e}', xbmc.LOGINFO)
        
        self.endDirectory('movies')
   
    def getOnlySeries(self):
        page = requests.get(f"{base_url}/sorozatok", headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')

        custom_tags = ['film-card-component','film-card-big-component']
        content_list = []
        for tag in soup.find_all(custom_tags):
            film_json = tag.get(':film')
            if film_json:
                film_json_clean = html.unescape(film_json)
                try:
                    parsed_film = json.loads(film_json_clean)
                    if parsed_film.get('type') == 1:
                        parsed_film['main_type'] = 'Film'
                    elif parsed_film.get('type') == 2:
                        parsed_film['main_type'] = 'Sorozat'
                    if parsed_film.get('language') == 'hu':
                        parsed_film['lang_type'] = 'Szinkronos'
                    else:
                        parsed_film['lang_type'] = 'Feliratos'
                    content_list.append(parsed_film)
                except json.JSONDecodeError as e:
                    print(f"Error decoding film JSON: {e}")
            
        for stuffs in content_list:
            slug_part = stuffs['slug']
            
            hun_title = stuffs['hungarian_title']
            lang_type = stuffs['lang_type']
            link_url = f'{base_url}/film/{slug_part}'
            
            img_part = stuffs['img']
            img_url = f'{base_url}{img_part}'
            
            content = stuffs['description']

            if lang_type == 'Feliratos':
                display_title = f'[B]{hun_title} - ([COLOR red]feliratos[/COLOR])[/B]'
            else:
                display_title = f'[B]{hun_title}[/B]'
            
            url_part = f'extract_series&url={quote_plus(link_url)}&img_url={img_url}&hun_title={quote_plus(hun_title)}&content={content}'
            self.addDirectoryItem(display_title, url_part, img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})
        
        try:
            pagination = soup.find('div', class_='flex-fill paginate mb-3')
            if pagination:
                next_page_link = pagination.find('a', {'aria-label': 'Next »'})
                if next_page_link:
                    next_page_url = next_page_link.get('href')
                    self.addDirectoryItem('[I]Következő oldal[/I]', f'series_items&url={quote_plus(next_page_url)}', '', 'DefaultFolder.png')
        except Exception as e:
            xbmc.log(f'{base_log_info}| getOnlyMovies | next_page_url | csak egy oldal található - {e}', xbmc.LOGINFO)
        
        self.endDirectory('series')      

    def getMovieItems(self, url, img_url, hun_title, content):
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')

        custom_tags = ['film-card-component','film-card-big-component']
        content_list = []
        for tag in soup.find_all(custom_tags):
            film_json = tag.get(':film')
            if film_json:
                film_json_clean = html.unescape(film_json)
                try:
                    parsed_film = json.loads(film_json_clean)
                    if parsed_film.get('type') == 1:
                        parsed_film['main_type'] = 'Film'
                    elif parsed_film.get('type') == 2:
                        parsed_film['main_type'] = 'Sorozat'
                    if parsed_film.get('language') == 'hu':
                        parsed_film['lang_type'] = 'Szinkronos'
                    else:
                        parsed_film['lang_type'] = 'Feliratos'
                    content_list.append(parsed_film)
                except json.JSONDecodeError as e:
                    print(f"Error decoding film JSON: {e}")
            
        for stuffs in content_list:
            slug_part = stuffs['slug']
            
            link_url = stuffs['url']
            
            hun_title = stuffs['hungarian_title']
            lang_type = stuffs['lang_type']
            
            img_part = stuffs['img']
            img_url = f'{base_url}{img_part}'
            
            content = stuffs['description']

            if lang_type == 'Feliratos':
                display_title = f'[B]{hun_title} - ([COLOR red]feliratos[/COLOR])[/B]'
            else:
                display_title = f'[B]{hun_title}[/B]'
            
            url_part = f'playmovie&url={quote_plus(link_url)}&img_url={img_url}&hun_title={quote_plus(hun_title)}&content={content}'
            self.addDirectoryItem(display_title, url_part, img_url, 'DefaultMovies.png', isFolder=False, meta={'title': hun_title, 'plot': content})
        
        try:
            pagination = soup.find('div', class_='flex-fill paginate mb-3')
            if pagination:
                next_page_link = pagination.find('a', {'aria-label': 'Next »'})
                if next_page_link:
                    next_page_url = next_page_link.get('href')
                    self.addDirectoryItem('[I]Következő oldal[/I]', f'movie_items&url={quote_plus(next_page_url)}', '', 'DefaultFolder.png')
        except Exception as e:
            xbmc.log(f'{base_log_info}| getOnlyMovies | next_page_url | csak egy oldal található - {e}', xbmc.LOGINFO)
        
        self.endDirectory('movies')

    def getSeriesItems(self, url, img_url, hun_title, content):
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')

        custom_tags = ['film-card-component','film-card-big-component']
        content_list = []
        for tag in soup.find_all(custom_tags):
            film_json = tag.get(':film')
            if film_json:
                film_json_clean = html.unescape(film_json)
                try:
                    parsed_film = json.loads(film_json_clean)
                    if parsed_film.get('type') == 1:
                        parsed_film['main_type'] = 'Film'
                    elif parsed_film.get('type') == 2:
                        parsed_film['main_type'] = 'Sorozat'
                    if parsed_film.get('language') == 'hu':
                        parsed_film['lang_type'] = 'Szinkronos'
                    else:
                        parsed_film['lang_type'] = 'Feliratos'
                    content_list.append(parsed_film)
                except json.JSONDecodeError as e:
                    print(f"Error decoding film JSON: {e}")
            
        for stuffs in content_list:
            slug_part = stuffs['slug']
            
            hun_title = stuffs['hungarian_title']
            lang_type = stuffs['lang_type']
            link_url = f'{base_url}/film/{slug_part}'
            
            img_part = stuffs['img']
            img_url = f'{base_url}{img_part}'
            
            content = stuffs['description']

            if lang_type == 'Feliratos':
                display_title = f'[B]{hun_title} - ([COLOR red]feliratos[/COLOR])[/B]'
            else:
                display_title = f'[B]{hun_title}[/B]'
            
            url_part = f'extract_series&url={quote_plus(link_url)}&img_url={img_url}&hun_title={quote_plus(hun_title)}&content={content}'
            self.addDirectoryItem(display_title, url_part, img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})
        
        try:
            pagination = soup.find('div', class_='flex-fill paginate mb-3')
            if pagination:
                next_page_link = pagination.find('a', {'aria-label': 'Next »'})
                if next_page_link:
                    next_page_url = next_page_link.get('href')
                    self.addDirectoryItem('[I]Következő oldal[/I]', f'series_items&url={quote_plus(next_page_url)}', '', 'DefaultFolder.png')
        except Exception as e:
            xbmc.log(f'{base_log_info}| getOnlyMovies | next_page_url | csak egy oldal található - {e}', xbmc.LOGINFO)
        
        self.endDirectory('series')

    def extractSeries(self, url, img_url, hun_title, content, ep_title):
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')
        container = soup.find('div', class_='flex-fill pt-1')
        
        episode_links = {}
        if container:
            for a in container.find_all('a', href=True):
                href = a['href']
                match = re.search(r'/(\d+)-evad/(\d+)-resz', href)
                if match:
                    season = int(match.group(1))
                    episode = int(match.group(2))
                    episode_key = f'S{season:02d}E{episode:02d}'
                    if episode_key not in episode_links:
                        episode_links[episode_key] = href
        
        episode_list = [{"episode": episode, "link": link} for episode, link in episode_links.items()]
        
        sorted_episode_list = sorted(episode_list, key=lambda x: (int(x["episode"][1:3]), int(x["episode"][4:6])))
        
        for stuffs in sorted_episode_list:
            
            ep_title = stuffs['episode']
            episode_link = stuffs['link']
            
            self.addDirectoryItem(f'[B]{ep_title} - {hun_title}[/B]', f'extract_episodes&url={quote_plus(episode_link)}&img_url={img_url}&hun_title={quote_plus(hun_title)}&content={content}&ep_title={quote_plus(ep_title)}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': ep_title, 'plot': content})             

        self.endDirectory('series')

    def extractEpisodes(self, url, img_url, hun_title, content, ep_title):
        html_soup_2 = requests.get(url, headers=headers)
        soup_2 = BeautifulSoup(html_soup_2.text, 'html.parser')

        iframe_component = soup_2.find('iframe-component')
        if iframe_component:
            raw_url = iframe_component.get(':url', '')
            iframe_src = raw_url.strip('"').replace('\\', '')
            
            self.addDirectoryItem(f'[B]{ep_title} - {hun_title}[/B]', f'playmovie&url={quote_plus(iframe_src)}&img_url={img_url}&hun_title={quote_plus(hun_title)}&content={content}&ep_title={quote_plus(ep_title)}', img_url, 'DefaultMovies.png', isFolder=False, meta={'title': f'{ep_title} - {hun_title}', 'plot': content})
        
        self.endDirectory('series')

    def playMovie(self, url, subtitle_link):
        if re.match(r'.*on[vid,mov].*', url):
        
            xbmc.log(f'{base_log_info}| playMovie | playing onvid: {url}', xbmc.LOGINFO)

            play_item = xbmcgui.ListItem(path=url)
            play_item.setProperty("User-Agent", "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36")
            play_item.setSubtitles([subtitle_link])
            
            xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=play_item)
        
        elif re.search('.*videa.*', url):
            
            STATIC_SECRET = 'xHb0ZvME5q8CBcoQi6AngerDu3FGO9fkUlwPmLVY_RTzj2hJIS4NasXWKy1td7p'
            
            def rc4(cipher_text, key):
                def compat_ord(c):
                    return c if isinstance(c, int) else ord(c)
            
                res = b''
            
                key_len = len(key)
                S = list(range(256))
            
                j = 0
                for i in range(256):
                    j = (j + S[i] + ord(key[i % key_len])) % 256
                    S[i], S[j] = S[j], S[i]
            
                i = 0
                j = 0
                for m in range(len(cipher_text)):
                    i = (i + 1) % 256
                    j = (j + S[i]) % 256
                    S[i], S[j] = S[j], S[i]
                    k = S[(S[i] + S[j]) % 256]
                    res += struct.pack('B', k ^ compat_ord(cipher_text[m]))
            
                if sys.version_info[0] == 3:
                    return res.decode()
                else:
                    return res
            
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            }
            
            session = requests.Session()
            response = session.get(url, cookies={"session_adult": "1"})
            
            video_page = response.text
            
            if '/player' in url:
                player_url = url
                player_page = video_page
            else:
                player_url = re.search(r'<iframe.*?src="(/player\?[^"]+)"', video_page).group(1)
                player_url = urljoin(url, player_url)
                response = session.get(player_url)
                player_page = response.text
            
            nonce = re.search(r'_xt\s*=\s*"([^"]+)"', player_page).group(1)
            
            l = nonce[:32]
            s = nonce[32:]
            result = ''
            for i in range(0, 32):
                result += s[i - (STATIC_SECRET.index(l[i]) - 31)]
            
            query = parse_qs(urlparse(player_url).query)
            
            random_seed = ''
            for i in range(8):
                random_seed += random.choice(string.ascii_letters + string.digits)
            
            _s = random_seed
            _t = result[:16]
            if 'f' in query or 'v' in query:
                _param = f'f={query["f"][0]}' if 'f' in query else f'v={query["v"][0]}'
            response = session.get(f'https://videa.hu/player/xml?platform=desktop&{_param}&_s={_s}&_t={_t}')
            
            videaXml = response.text
            if not videaXml.startswith('<?xml'):
                key = result[16:] + random_seed + response.headers['x-videa-xs']
                videaXml = rc4(base64.b64decode(videaXml), key)            
            
            try:        
                videaData = xmltodict.parse(videaXml)

                sources = videaData["videa_video"]["video_sources"]["video_source"]
                if isinstance(sources, list):
                    sorted_sources = sorted(sources, key=lambda x: int(x["@width"]), reverse=True)
                else:
                    sorted_sources = [sources]

                selected_source = sorted_sources[0]
                s_format = selected_source["@name"]
                s_url = selected_source["#text"]
                s_exp = selected_source["@exp"]

                hash_key = "hash_value_" + s_format
                hash_x_key = videaData["videa_video"]["hash_values"][hash_key]
                video_url = f'https:{s_url}?md5={hash_x_key}&expires={s_exp}'
                
                xbmc.log(f'{base_log_info}| playMovie | video_url: {video_url}', xbmc.LOGINFO)

                play_item = xbmcgui.ListItem(path=video_url)

                try:
                    subtitles = videaData["videa_video"]["subtitles"]["subtitle"]
                    subtitle_urls = []
            
                    if isinstance(subtitles, list):
                        for subtitle in subtitles:
                            subtitle_url = 'https:' + subtitle["@src"]
                            subtitle_urls.append(subtitle_url)
                    else:
                        subtitle_url = 'https:' + subtitles["@src"]
                        subtitle_urls.append(subtitle_url)

                    play_item.setSubtitles(subtitle_urls)
                    xbmc.log(f'{base_log_info}| playMovie | subtitles: {subtitle_urls}', xbmc.LOGINFO)
                except KeyError:
                    xbmc.log(f'{base_log_info}| playMovie | No subtitles found', xbmc.LOGINFO)

                xbmcplugin.setResolvedUrl(syshandle, True, listitem=play_item)
                
            except Exception as e:
                xbmc.log(f'{base_log_info}| playMovie | Error: {str(e)}', xbmc.LOGINFO)
                notification = xbmcgui.Dialog()
                notification.notification("Mozikatalogus", "Törölt tartalom", time=5000)

        else:
            try:
                direct_url = urlresolver.resolve(url)
                
                xbmc.log(f'{base_log_info}| playMovie | direct_url: {direct_url}', xbmc.LOGINFO)
                play_item = xbmcgui.ListItem(path=direct_url)
                xbmcplugin.setResolvedUrl(syshandle, True, listitem=play_item)
            except:
                xbmc.log(f'{base_log_info}| playMovie | name: No video sources found', xbmc.LOGINFO)
                notification = xbmcgui.Dialog()
                notification.notification("Mozikatalogus", "Törölt tartalom", time=5000)

    def getSearches(self):
        self.addDirectoryItem('[COLOR lightgreen]Új keresés[/COLOR]', 'newsearch', '', 'DefaultFolder.png')
        try:
            file = open(self.searchFileName, "r")
            olditems = file.read().splitlines()
            file.close()
            items = list(set(olditems))
            items.sort(key=locale.strxfrm)
            if len(items) != len(olditems):
                file = open(self.searchFileName, "w")
                file.write("\n".join(items))
                file.close()
            for item in items:
                url_p = f"{base_url}/filmkereso?film_name={item}&type=&imdb%5B%5D=&imdb%5B%5D=&release_date_min=&release_date_max="
                enc_url = quote_plus(url_p)                
                self.addDirectoryItem(item, f'items&url={url_p}', '', 'DefaultFolder.png')

            if len(items) > 0:
                self.addDirectoryItem('[COLOR red]Keresési előzmények törlése[/COLOR]', 'deletesearchhistory', '', 'DefaultFolder.png')
        except:
            pass
        self.endDirectory()

    def deleteSearchHistory(self):
        if os.path.exists(self.searchFileName):
            os.remove(self.searchFileName)

    def doSearch(self):
        search_text = self.getSearchText()
        if search_text != '':
            if not os.path.exists(self.base_path):
                os.mkdir(self.base_path)
            file = open(self.searchFileName, "a")
            file.write(f"{search_text}\n")
            file.close()
            url = f"{base_url}/filmkereso?film_title2={search_text}&film_type=0&language=all&imdb_min=&imdb_max=&release_date_min=&release_date_max=&category_in=%5B%5D&category_not_in=%5B%5D"
            self.getItems(url)

    def getActorSearches(self):
        self.addDirectoryItem('[COLOR lightgreen]Új keresés[/COLOR]', 'actor_newsearch', '', 'DefaultFolder.png')
        try:
            file = open(self.searchFileName, "r")
            olditems = file.read().splitlines()
            file.close()
            items = list(set(olditems))
            items.sort(key=locale.strxfrm)
            if len(items) != len(olditems):
                file = open(self.searchFileName, "w")
                file.write("\n".join(items))
                file.close()
            for item in items:
                url_p = f"{base_url}/szineszek?searching_param={item}&search="
                enc_url = quote_plus(url_p)                
                self.addDirectoryItem(item, f'actor_items&url={url_p}', '', 'DefaultFolder.png')

            if len(items) > 0:
                self.addDirectoryItem('[COLOR red]Keresési előzmények törlése[/COLOR]', 'deletesearchhistory', '', 'DefaultFolder.png')
        except:
            pass
        self.endDirectory()
    
    def doActorSearch(self):
        search_text = self.getSearchText()
        if search_text != '':
            if not os.path.exists(self.base_path):
                os.mkdir(self.base_path)
            with open(self.searchFileName, "a") as file:
                file.write(f"{search_text}\n")
            quoted_text = quote_plus(search_text)
            url = f"{base_url}/szineszek?searching_param={quoted_text}&search="
            self.getActorItems(url)          

    def getSearchText(self):
        search_text = ''
        keyb = xbmc.Keyboard('', u'Add meg a keresend\xF5 film c\xEDm\xE9t')
        keyb.doModal()
        if keyb.isConfirmed():
            search_text = keyb.getText()
        return search_text

    def addDirectoryItem(self, name, query, thumb, icon, context=None, queue=False, isAction=True, isFolder=True, Fanart=None, meta=None, banner=None):
        url = f'{sysaddon}?action={query}' if isAction else query
        if thumb == '':
            thumb = icon
        cm = []
        if queue:
            cm.append((queueMenu, f'RunPlugin({sysaddon}?action=queueItem)'))
        if not context is None:
            cm.append((context[0].encode('utf-8'), f'RunPlugin({sysaddon}?action={context[1]})'))
        item = xbmcgui.ListItem(label=name)
        item.addContextMenuItems(cm)
        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': thumb, 'banner': banner})
        if Fanart is None:
            Fanart = addonFanart
        item.setProperty('Fanart_Image', Fanart)
        if not isFolder:
            item.setProperty('IsPlayable', 'true')
        if not meta is None:
            item.setInfo(type='Video', infoLabels=meta)
        xbmcplugin.addDirectoryItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)

    def endDirectory(self, type='addons'):
        xbmcplugin.setContent(syshandle, type)
        xbmcplugin.endOfDirectory(syshandle, cacheToDisc=True)
