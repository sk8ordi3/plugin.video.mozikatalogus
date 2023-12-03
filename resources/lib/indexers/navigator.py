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
import re

sysaddon = sys.argv[0]
syshandle = int(sys.argv[1])
addonFanart = xbmcaddon.Addon().getAddonInfo('fanart')

import platform
import xml.etree.ElementTree as ET

os_info = platform.platform()
kodi_version = xbmc.getInfoLabel('System.BuildVersion')

current_directory = os.path.dirname(os.path.abspath(__file__))
parent_directory = os.path.dirname(os.path.dirname(os.path.dirname(current_directory)))
addon_xml_path = os.path.join(parent_directory, "addon.xml")

tree = ET.parse(addon_xml_path)
root = tree.getroot()
version = root.attrib.get("version")

xbmc.log(f'Mozikatalogus | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info}', xbmc.LOGINFO)

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
            {"category_link": "https://mozikatalogus.hu/filmek-es-sorozatok/2022-2023", "category_title": "Megjelent 2022-2023"},
            {"category_link": "https://mozikatalogus.hu/nepszeru-filmek-es-sorozatok", "category_title": "Népszerű"},
            {"category_link": "https://mozikatalogus.hu/legjobbra-ertekelt-filmek-es-sorozatok", "category_title": "Legjobbra értékelt"},
            {"category_link": "https://mozikatalogus.hu/legujabb-filmek-es-sorozatok", "category_title": "Legfrissebb"},
            {"category_link": "https://mozikatalogus.hu/zs-filmek-es-sorozatok", "category_title": "Zs Filmek"},
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

        lang_series_list = []  

        for datas_div in soup.find_all('div', class_='datas'):
            lang_series = re.findall(r'language-img.*\s.*?>(.*)<', str(datas_div))[0].strip()
            lang_series_list.append(lang_series)

        for index, movie_div in enumerate(soup.find_all('div', class_='film-card')):
            link_url = base_url + movie_div.find_parent('a')['href']
            img_url = base_url + movie_div['data-src']
            hun_title = movie_div.find('h2', class_='title').get_text(strip=True)
        
            tartalom_style = movie_div.find('style').get_text()
            tartalom_matches = re.findall(r'content:\s*\'(.*?)\'', tartalom_style)
            content = tartalom_matches[0].strip() if tartalom_matches else None
            
            labels = movie_div.find_all('div', class_='label-text white')
            for label in labels:
                type = label.text.strip()

            lang_series = lang_series_list[index]
        
            if type == 'film':
                
                type = f'{type:^10}'
                
                if lang_series == 'felirat':
                    lang_suffix = f' - ([COLOR red]feliratos[/COLOR])'
                
                    self.addDirectoryItem(f'[B]|{type}| {hun_title}{lang_suffix}[/B]', f'extract_movie&url={quote_plus(link_url)}&img_url={img_url}&hun_title={hun_title}&content={content}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})
                else:    
                    self.addDirectoryItem(f'[B]|{type}| {hun_title}[/B]', f'extract_movie&url={quote_plus(link_url)}&img_url={img_url}&hun_title={hun_title}&content={content}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})
            else:
                
                if lang_series == 'felirat':
                    lang_suffix = f' - ([COLOR red]feliratos[/COLOR])'
                
                    self.addDirectoryItem(f'[B]|{type}| {hun_title}{lang_suffix}[/B]', f'extract_series&url={quote_plus(link_url)}&img_url={img_url}&hun_title={hun_title}&content={content}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})
                else:    
                    self.addDirectoryItem(f'[B]|{type}| {hun_title}[/B]', f'extract_series&url={quote_plus(link_url)}&img_url={img_url}&hun_title={hun_title}&content={content}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})
        
        try:
            next_page_link = soup.find('a', {'rel': 'next'})
            if next_page_link:
                next_page_url = next_page_link.get('href')
                self.addDirectoryItem('[I]Következő oldal[/I]', f'items&url={quote_plus(next_page_url)}', '', 'DefaultFolder.png')
        except AttributeError:
            xbmc.log(f'Mozikatalogus | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info} | getOnlyMovies | next_page_url | csak egy oldal található', xbmc.LOGINFO)
        
        self.endDirectory('movies')

    #szinesz
    def getActorItems(self, url):

        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')
        
        for actor_link in soup.find_all('a', class_='actorlink'):
            
            link =  base_url + actor_link['href']
            
            actor_img_url = actor_link.find('div', class_='actor-card')['style'].split("'")[1]
            
            label_text = actor_link.find('div', class_='label-text').get_text(strip=True)
            span_text = actor_link.find('div', class_='label-text').find('span').get_text(strip=True)            
            
            content = f'{span_text}'
            
            actor_name = actor_link.find('div', class_='actor-name').get_text(strip=True)
            
            self.addDirectoryItem(f'[B]{actor_name} - {span_text}[/B]', f'items&url={quote_plus(link)}', actor_img_url, 'DefaultMovies.png', isFolder=True, meta={'title': actor_name})
        
        try:
            next_page_link = soup.find('a', {'rel': 'next'})
            if next_page_link:
                next_page_url = next_page_link.get('href')
                self.addDirectoryItem('[I]Következő oldal[/I]', f'actor_items&url={quote_plus(next_page_url)}', '', 'DefaultFolder.png')
        except AttributeError:
            xbmc.log(f'Mozikatalogus | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info} | getActorItems | next_page_url | csak egy oldal található', xbmc.LOGINFO)
        
        self.endDirectory('movies')
    
    def getOnlyMovies(self):
        page = requests.get(f"{base_url}/filmek", headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')

        lang_series_list = []

        for datas_div in soup.find_all('div', class_='datas'):
            lang_series = re.findall(r'language-img.*\s.*?>(.*)<', str(datas_div))[0].strip()
            lang_series_list.append(lang_series)

        for index, movie_div in enumerate(soup.find_all('div', class_='film-card')):
            link_url = base_url + movie_div.find_parent('a')['href']
            img_url = base_url + movie_div['data-src']
            hun_title = movie_div.find('h2', class_='title').get_text(strip=True)
        
            tartalom_style = movie_div.find('style').get_text()
            tartalom_matches = re.findall(r'content:\s*\'(.*?)\'', tartalom_style)
            content = tartalom_matches[0].strip() if tartalom_matches else None

            lang_series = lang_series_list[index]
        
            if lang_series == 'felirat':
                lang_suffix = f' - ([COLOR red]feliratos[/COLOR])'
                
                self.addDirectoryItem(f'[B]{hun_title}{lang_suffix}[/B]', f'extract_movie&url={quote_plus(link_url)}&img_url={img_url}&hun_title={quote_plus(hun_title)}&content={content}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})
            else:
                self.addDirectoryItem(f'[B]{hun_title}[/B]', f'extract_movie&url={quote_plus(link_url)}&img_url={img_url}&hun_title={quote_plus(hun_title)}&content={content}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})

        try:
            next_page_link = soup.find('a', {'rel': 'next'})
            if next_page_link:
                next_page_url = next_page_link.get('href')
                self.addDirectoryItem('[I]Következő oldal[/I]', f'movie_items&url={quote_plus(next_page_url)}', '', 'DefaultFolder.png')
        except AttributeError:
            xbmc.log(f'Mozikatalogus | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info} | getOnlyMovies | next_page_url | csak egy oldal található', xbmc.LOGINFO)
        
        self.endDirectory('movies')

    def extractMovie(self, url, img_url, hun_title, content):
        
        response_2 = requests.get(url, headers=headers)
        soup_2 = BeautifulSoup(response_2.text, 'html.parser')
        
        iframe_tag = soup_2.find('iframe')
        if iframe_tag:
            iframe_src = iframe_tag.get('src')
            xbmc.log(f'Mozikatalogus | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info} | extractMovie | iframe_src | {iframe_src}', xbmc.LOGINFO)
            
        self.addDirectoryItem(f'[B]{hun_title}[/B]', f'playmovie&url={quote_plus(iframe_src)}&img_url={img_url}&hun_title={quote_plus(hun_title)}&content={content}', img_url, 'DefaultMovies.png', isFolder=False, meta={'title': hun_title, 'plot': content})
        
        self.endDirectory('series')    

    def getOnlySeries(self):
        page = requests.get(f"{base_url}/sorozatok", headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')

        lang_series_list = []

        for datas_div in soup.find_all('div', class_='datas'):
            lang_series = re.findall(r'language-img.*\s.*?>(.*)<', str(datas_div))[0].strip()
            lang_series_list.append(lang_series)

        for index, movie_div in enumerate(soup.find_all('div', class_='film-card')):
            link_url = base_url + movie_div.find_parent('a')['href']
            img_url = base_url + movie_div['data-src']
            hun_title = movie_div.find('h2', class_='title').get_text(strip=True)
        
            tartalom_style = movie_div.find('style').get_text()
            tartalom_matches = re.findall(r'content:\s*\'(.*?)\'', tartalom_style)
            content = tartalom_matches[0].strip() if tartalom_matches else None

            lang_series = lang_series_list[index]
        
            if lang_series == 'felirat':
                lang_suffix = f' - ([COLOR red]feliratos[/COLOR])'
                
                self.addDirectoryItem(f'[B]{hun_title}{lang_suffix}[/B]', f'extract_series&url={quote_plus(link_url)}&img_url={img_url}&hun_title={quote_plus(hun_title)}&content={content}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})
            else:
                self.addDirectoryItem(f'[B]{hun_title}[/B]', f'extract_series&url={quote_plus(link_url)}&img_url={img_url}&hun_title={quote_plus(hun_title)}&content={content}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})
        
        try:
            next_page_link = soup.find('a', {'rel': 'next'})
            if next_page_link:
                next_page_url = next_page_link.get('href')
                self.addDirectoryItem('[I]Következő oldal[/I]', f'series_items&url={quote_plus(next_page_url)}', '', 'DefaultFolder.png')
        except AttributeError:
            xbmc.log(f'Mozikatalogus | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info} | getOnlySeries | next_page_url | csak egy oldal található', xbmc.LOGINFO)
        
        self.endDirectory('series')      

    def getMovieItems(self, url, img_url, hun_title, content):
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')

        lang_series_list = []

        for datas_div in soup.find_all('div', class_='datas'):
            lang_series = re.findall(r'language-img.*\s.*?>(.*)<', str(datas_div))[0].strip()
            lang_series_list.append(lang_series)

        for index, movie_div in enumerate(soup.find_all('div', class_='film-card')):
            link_url = base_url + movie_div.find_parent('a')['href']
            img_url = base_url + movie_div['data-src']
            hun_title = movie_div.find('h2', class_='title').get_text(strip=True)
        
            tartalom_style = movie_div.find('style').get_text()

            tartalom_matches = re.findall(r'content:\s*\'(.*?)\'', tartalom_style)
            content = tartalom_matches[0].strip() if tartalom_matches else None

            lang_series = lang_series_list[index]
        
            if lang_series == 'felirat':
                lang_suffix = f' - ([COLOR red]feliratos[/COLOR])'
            
                self.addDirectoryItem(f'[B]{hun_title}{lang_suffix}[/B]', f'extract_movie&url={quote_plus(link_url)}&img_url={img_url}&hun_title={hun_title}&content={content}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})
            else:    
                self.addDirectoryItem(f'[B]{hun_title}[/B]', f'extract_movie&url={quote_plus(link_url)}&img_url={img_url}&hun_title={hun_title}&content={content}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})
        
        try:
            next_page_link = soup.find('a', {'rel': 'next'})
            if next_page_link:
                next_page_url = next_page_link.get('href')
                self.addDirectoryItem('[I]Következő oldal[/I]', f'movie_items&url={quote_plus(next_page_url)}', '', 'DefaultFolder.png')
        except AttributeError:
            xbmc.log(f'Mozikatalogus | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info} | getOnlyMovies | next_page_url | csak egy oldal található', xbmc.LOGINFO)
        
        self.endDirectory('movies')

    def getSeriesItems(self, url, img_url, hun_title, content):
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')

        lang_series_list = []

        for datas_div in soup.find_all('div', class_='datas'):
            lang_series = re.findall(r'language-img.*\s.*?>(.*)<', str(datas_div))[0].strip()
            lang_series_list.append(lang_series)

        for index, movie_div in enumerate(soup.find_all('div', class_='film-card')):
            link_url = base_url + movie_div.find_parent('a')['href']
            img_url = base_url + movie_div['data-src']
            hun_title = movie_div.find('h2', class_='title').get_text(strip=True)
        
            tartalom_style = movie_div.find('style').get_text()
            tartalom_matches = re.findall(r'content:\s*\'(.*?)\'', tartalom_style)
            content = tartalom_matches[0].strip() if tartalom_matches else None

            lang_series = lang_series_list[index]
        
            if lang_series == 'felirat':
                lang_suffix = f' - ([COLOR red]feliratos[/COLOR])'
                
                self.addDirectoryItem(f'[B]{hun_title}{lang_suffix}[/B]', f'extract_series&url={quote_plus(link_url)}&img_url={img_url}&hun_title={quote_plus(hun_title)}&content={content}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})
            else:
                self.addDirectoryItem(f'[B]{hun_title}[/B]', f'extract_series&url={quote_plus(link_url)}&img_url={img_url}&hun_title={quote_plus(hun_title)}&content={content}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': hun_title, 'plot': content})
            
        try:
            next_page_link = soup.find('a', {'rel': 'next'})
            if next_page_link:
                next_page_url = next_page_link.get('href')
                self.addDirectoryItem('[I]Következő oldal[/I]', f'series_items&url={quote_plus(next_page_url)}', '', 'DefaultFolder.png')
        except AttributeError:
            xbmc.log(f'Mozikatalogus | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info} | getOnlyMovies | next_page_url | csak egy oldal található', xbmc.LOGINFO)
        
        self.endDirectory('series')

    def extractSeries(self, url, img_url, hun_title, content, ep_title):
        html_soup_2 = requests.get(url, headers=headers)
        soup_2 = BeautifulSoup(html_soup_2.text, 'html.parser')
        tab_panes = soup_2.find_all('div', {'class': 'tab-pane'})
        
        for tab_pane in tab_panes:
            season_number = tab_pane['id'].replace('tab', '')
            episodes = tab_pane.find_all('li')
        
            for episode in episodes:
                episode_link = 'https://mozikatalogus.hu' + episode.find('a')['href']
                episode_text = int(episode.text.strip())
                episode_season_num = int(episode_link.split('-evad/')[0].split('/')[-1])
                ep_title = f'S{episode_season_num:02d}E{episode_text:02d} - {hun_title}'
                
                self.addDirectoryItem(f'[B]S{episode_season_num:02d}E{episode_text:02d} - {hun_title}[/B]', f'extract_episodes&url={quote_plus(episode_link)}&img_url={img_url}&hun_title={quote_plus(hun_title)}&content={content}&ep_title={quote_plus(ep_title)}', img_url, 'DefaultMovies.png', isFolder=True, meta={'title': ep_title, 'plot': content})             

        self.endDirectory('series')

    def extractEpisodes(self, url, img_url, hun_title, content, ep_title):
    
        html_soup_2 = requests.get(url, headers=headers)
        soup_2 = BeautifulSoup(html_soup_2.text, 'html.parser')

        iframe = soup_2.find('iframe')

        if iframe:
            iframe_src = iframe.get('src')
            xbmc.log(f'Mozikatalogus | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info} | extractEpisodes | iframe_src | {iframe_src}', xbmc.LOGINFO)

            if re.match(r'.*on[vid,mov].*', iframe_src):
                #https://onmov.me/embed/G9bG/ # 1. "rossz" > átalakítás: https://onvid.hu/embed/G9bG/
                change_embed = re.findall(r'(/embed.*)', str(iframe_src))[0].strip()
                onvid = f'https://onvid.hu{change_embed}'
                
                html_soup_3 = requests.get(onvid, headers=headers)
                soup_3 = BeautifulSoup(html_soup_3.text, 'html.parser')
                
                video_link = soup_3.find('source')['src']
                subtitle_link = soup_3.find('track')['src']
                
                self.addDirectoryItem(f'[B]|onvid|{ep_title}[/B]', f'playmovie&url={quote_plus(video_link)}&img_url={img_url}&hun_title={quote_plus(hun_title)}&content={content}&ep_title={quote_plus(ep_title)}&subtitle_link={subtitle_link}', img_url, 'DefaultMovies.png', isFolder=False, meta={'title': ep_title, 'plot': content})
            
            else:
                #everything else           
                self.addDirectoryItem(f'[B]{ep_title}[/B]', f'playmovie&url={quote_plus(iframe_src)}&img_url={img_url}&hun_title={quote_plus(hun_title)}&content={content}&ep_title={quote_plus(ep_title)}', img_url, 'DefaultMovies.png', isFolder=False, meta={'title': ep_title, 'plot': content})
        
        self.endDirectory('series')

    def playMovie(self, url, subtitle_link):
        
        if re.match(r'.*on[vid,mov].*', url):
        
            xbmc.log(f'Mozikatalogus | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info} | playMovie | playing onvid: {url}', xbmc.LOGINFO)

            play_item = xbmcgui.ListItem(path=url)
            play_item.setProperty("User-Agent", "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36")
            play_item.setSubtitles([subtitle_link])
            
            xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=play_item)
        
        else:
            try:
                direct_url = urlresolver.resolve(url)
                
                xbmc.log(f'Mozikatalogus | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info} | playMovie | direct_url: {direct_url}', xbmc.LOGINFO)
                play_item = xbmcgui.ListItem(path=direct_url)
                xbmcplugin.setResolvedUrl(syshandle, True, listitem=play_item)
            except:
                xbmc.log(f'Mozikatalogus | v{version} | Kodi: {kodi_version[:5]}| OS: {os_info} | playMovie | name: No video sources found', xbmc.LOGINFO)
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
            url = f"{base_url}/filmkereso?film_name={search_text}&type=&imdb%5B%5D=&imdb%5B%5D=&release_date_min=&release_date_max="
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
                url_p = f"{base_url}/szineszek?name={item}&save="
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
            file = open(self.searchFileName, "a")
            file.write(f"{search_text}\n")
            file.close()
            url = f"{base_url}/szineszek?name={search_text}&save="
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