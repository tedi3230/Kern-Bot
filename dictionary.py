import asyncio
from os import environ
import re
import json

import aiohttp
import async_timeout
import discord
from discord.ext import commands

#Finally


class Dictionary:
    def __init__(self, bot):
        self.bot = bot
        self.bot_logs = self.bot.get_channel(382780308610744331)
        self.dictionary_base_URL = 'https://od-api.oxforddictionaries.com/api/v1/entries/en/{}'
        self.image_base_url = 'https://duckduckgo.com/'
        try:
            app_id = environ["APP_ID"]
            app_key = environ["APP_KEY"]
        except KeyError:
            with open("client_secret.txt", encoding="utf-8") as file:
                lines = [l.strip() for l in file]
                app_id = lines[1]
                app_key = lines[2]
        self.headers = {"Accept": "application/json",
                        "app_id": app_id,
                        "app_key": app_key}

    async def _result_parser(self, results : list):
        for lexicalEntry in results:
            for entry in lexicalEntry['entries']:
                for sense in entry['senses']:
                    if 'domains' in sense:
                        domains = sense['domains']
                    else:
                        domains = []
                    if 'examples' in sense:
                        examples = sense['examples']
                    else:
                        examples = []
                    yield [lexicalEntry['lexicalCategory'], domains, sense['definitions'], examples]
                    if 'subsenses' in sense:
                        for subsense in sense['subsenses']:
                            if 'domains' in subsense:
                                domains = subsense['domains']
                            else:
                                domains = []
                            if 'examples' in subsense:
                                examples = subsense['examples']
                            else:
                                examples = []
                            yield [lexicalEntry['lexicalCategory'], domains, subsense['definitions'], examples]

    async def _get_dic_request(self, url):
        async with aiohttp.ClientSession() as session:
            with async_timeout.timeout(10):
                async with session.get(url, headers=self.headers) as response:
                    if not response.status == 200:
                        return
                    json = await response.json()
                    return json['results']

    async def _get_key(self, term):
        parameters = {'q': term}
        async with aiohttp.ClientSession() as session:
            with async_timeout.timeout(10):
                async with session.post(self.image_base_url, data=parameters) as response:
                    text_response = await response.text()
            return re.search(r'vqd=(\d+)\&', text_response, re.M|re.I)

    async def _get_image(self, term):
        search_obj = await self._get_key(term)
        params = (
            ('l', 'wt-wt'),
            ('o', 'json'),
            ('q', term),
            ('vqd', search_obj.group(1)),
            ('f', ',,,'),
            ('p', '2')
        )
        async with aiohttp.ClientSession() as session:
            with async_timeout.timeout(10):
                async with session.get(self.image_base_url + "i.js",params=params) as response:
                    json_response = json.loads(await response.text())
                    results = json_response['results']
            return results[0]['image']

    async def _word_not_found(self, term):
        results = await self._get_dic_request("https://od-api.oxforddictionaries.com/api/v1/search/en?q={}&prefix=false&limit=5".format(term))
        similar_words = [match['word'] for match in results]
        similar_words = ["[{}](https://en.oxforddictionaries.com/definition/{})".format(term.capitalize(), "_".join(term.split())) for term in similar_words]
        print(similar_words)
        embed = discord.Embed(title="Error:", description="No matches found for `{}`.".format(term), colour=0xff0000)
        if bool(similar_words):
            embed.add_field(name="Did you mean?", value="\n".join(similar_words))
        return embed

    @commands.command(aliases=['synonyms','s'])
    async def synonym(self, ctx, term):
        await ctx.trigger_typing()
        if len(term.split()) > 1:
            term = "_".join(term.split())
        data = await self._get_dic_request(self.dictionary_base_URL.format(term.lower()) + "/synonyms")
        if data is None:
            await ctx.send(embed=await self._word_not_found(term))
            return

        lexical_entries = data[0]['lexicalEntries']
        lexicon = dict()
        for entry in lexical_entries:
            lexicon[entry['lexicalCategory']] = [synonym['text'] for synonym in entry['entries'][0]['senses'][0]['synonyms']]
        embed = discord.Embed(title="Synonyms: {}".format(term.capitalize(), colour=0x00ff00, url='https://en.oxforddictionaries.com/thesaurus/{}'.format(term)))
        for category, synonyms in lexicon.items():
            synonym_list = ["[{}](https://en.oxforddictionaries.com/definition/{})".format(term.capitalize(), "_".join(term.split())) for term in synonyms[:5:]]
            if len(synonym_list) > 1:
                category+="s:"
            embed.add_field(name=category.capitalize(), value="\n".join(synonym_list))
        embed.set_author(name="Oxford Dictionary", url="https://en.oxforddictionaries.com/", icon_url='https://en.oxforddictionaries.com/apple-touch-icon-180x180.png')

        await ctx.send(embed=embed)     

    @commands.command(aliases=['antonyms','a'])
    async def antonym(self, ctx, term):
        await ctx.trigger_typing()
        if len(term.split()) > 1:
            term = "_".join(term.split())
        data = await self._get_dic_request(self.dictionary_base_URL.format(term.lower()) + "/antonyms")
        if data is None:
            await ctx.send(embed=await self._word_not_found(term))
            return

        lexical_entries = data[0]['lexicalEntries']
        lexicon = dict()
        for entry in lexical_entries:
            lexicon[entry['lexicalCategory']] = [antonym['text'] for antonym in entry['entries'][0]['senses'][0]['antonyms']]
        embed = discord.Embed(title="antonyms: {}".format(term.capitalize(), colour=0x00ff00, url='https://en.oxforddictionaries.com/thesaurus/{}'.format(term)))
        for category, antonyms in lexicon.items():
            antonym_list = ["[{}](https://en.oxforddictionaries.com/definition/{})".format(term.capitalize(), "_".join(term.split())) for term in antonyms[:5:]]
            if len(antonym_list) > 1:   
                category+="s:"
            embed.add_field(name=category.capitalize(), value="\n".join(antonym_list))
        embed.set_author(name="Oxford Dictionary", url="https://en.oxforddictionaries.com/", icon_url='https://en.oxforddictionaries.com/apple-touch-icon-180x180.png')

        await ctx.send(embed=embed)   

    @commands.command(aliases=['define','d'])
    async def meaning(self, ctx, term):
        await ctx.trigger_typing()
        if len(term.split()) > 1:
            term = "_".join(term.split())
        data = await self._get_dic_request(self.dictionary_base_URL.format(term.lower()))
        if data is None:
            await ctx.send(embed=await self._word_not_found(term))
            return

        results = data[0]['lexicalEntries']
        category_list = {}

        async for definition in self._result_parser(results):
            if definition[0] in category_list:
                category_list[definition[0]].append(definition)
            else:
                category_list[definition[0]] = [definition]

        embed = discord.Embed(colour=0x00ff00, url='https://en.oxforddictionaries.com/definition/{}'.format("_".join(term.split())))

        for lexical_category, definitions in category_list.items():
            value = ""
            for definition in definitions:
                for domain in definition[1]:
                    value += "*{}*, ".format(domain)
                value += definition[2][0].capitalize()
                for example in definition[3]:
                    value += "\n*{}.*".format(example['text'].capitalize())
                value += "\n\n"
            embed.add_field(name=lexical_category, value=value, inline=False)

        ipa_string = str()
        for entry in results:
            if 'pronunications' in entry:
                for pronunciation in entry['pronunciations']:   
                    ipa_string += "**{}:** {}\n".format(entry['lexicalCategory'], pronunciation['phoneticSpelling'])
                embed.add_field(name="Pronunciation", value=ipa_string)

        if 'etymologies' in data[0]["lexicalEntries"][0]['entries'][0]:
            etymology = data[0]["lexicalEntries"][0]['entries'][0]['etymologies'][0]
            print(etymology)
            embed.add_field(name="Word Origin:", value=etymology)
        

        if len(category_list) == 1 and next(iter(category_list)) == "Residual":
            url_term = term.upper()
        else:
            url_term = term.capitalize()

        embed.set_author(name="{}".format(url_term), url='https://en.oxforddictionaries.com/definition/{}'.format("_".join(term.split())))
        
        embed.set_thumbnail(url=await self._get_image(term))
        embed.set_footer(text="Requested by: {} | Results provided by the Oxford Dictionary".format(ctx.message.author), icon_url='https://en.oxforddictionaries.com/apple-touch-icon-180x180.png')
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Dictionary(bot))


"Example return define http://json.parser.online.fr/beta/"
{
  "metadata": {
    "provider": "Oxford University Press"
  },
  "results": [
    {
      "id": "ace",
      "language": "en",
      "lexicalEntries": [
        {
          "entries": [
            {
              "etymologies": [
                "Middle English (denoting the ‘one’ on dice): via Old French from Latin as ‘unity, a unit’"
              ],
              "grammaticalFeatures": [
                {
                  "text": "Singular",
                  "type": "Number"
                }
              ],
              "homographNumber": "000",
              "senses": [
                {
                  "definitions": [
                    "a playing card with a single spot on it, ranked as the highest card in its suit in most card games"
                  ],
                  "domains": [
                    "Cards"
                  ],
                  "examples": [
                    {
                      "registers": [
                        "figurative"
                      ],
                      "text": "life had started dealing him aces again"
                    },
                    {
                      "text": "the ace of diamonds"
                    }
                  ],
                  "id": "m_en_gbus0005680.006"
                },
                {
                  "definitions": [
                    "a person who excels at a particular sport or other activity"
                  ],
                  "domains": [
                    "Sport"
                  ],
                  "examples": [
                    {
                      "text": "a motorcycle ace"
                    }
                  ],
                  "id": "m_en_gbus0005680.010",
                  "registers": [
                    "informal"
                  ],
                  "subsenses": [
                    {
                      "definitions": [
                        "a pilot who has shot down many enemy aircraft"
                      ],
                      "domains": [
                        "Air Force"
                      ],
                      "examples": [
                        {
                          "text": "a Battle of Britain ace"
                        }
                      ],
                      "id": "m_en_gbus0005680.011"
                    }
                  ]
                },
                {
                  "definitions": [
                    "(in tennis and similar games) a service that an opponent is unable to return and thus wins a point"
                  ],
                  "domains": [
                    "Tennis"
                  ],
                  "examples": [
                    {
                      "text": "Nadal banged down eight aces in the set"
                    }
                  ],
                  "id": "m_en_gbus0005680.013",
                  "subsenses": [
                    {
                      "definitions": [
                        "a hole in one"
                      ],
                      "domains": [
                        "Golf"
                      ],
                      "examples": [
                        {
                          "text": "his hole in one at the 15th was Senior's second ace as a professional"
                        }
                      ],
                      "id": "m_en_gbus0005680.014",
                      "registers": [
                        "informal"
                      ]
                    }
                  ]
                }
              ]
            }
          ],
          "language": "en",
          "lexicalCategory": "Noun",
          "pronunciations": [
            {
              "audioFile": "http://audio.oxforddictionaries.com/en/mp3/ace_gb_1.mp3",
              "dialects": [
                "British English"
              ],
              "phoneticNotation": "IPA",
              "phoneticSpelling": "eɪs"
            }
          ],
          "text": "ace"
        },
        {
          "entries": [
            {
              "grammaticalFeatures": [
                {
                  "text": "Positive",
                  "type": "Degree"
                }
              ],
              "homographNumber": "001",
              "senses": [
                {
                  "definitions": [
                    "very good"
                  ],
                  "examples": [
                    {
                      "text": "Ace! You've done it!"
                    },
                    {
                      "text": "an ace swimmer"
                    }
                  ],
                  "id": "m_en_gbus0005680.016",
                  "registers": [
                    "informal"
                  ]
                }
              ]
            }
          ],
          "language": "en",
          "lexicalCategory": "Adjective",
          "pronunciations": [
            {
              "audioFile": "http://audio.oxforddictionaries.com/en/mp3/ace_gb_1.mp3",
              "dialects": [
                "British English"
              ],
              "phoneticNotation": "IPA",
              "phoneticSpelling": "eɪs"
            }
          ],
          "text": "ace"
        },
        {
          "entries": [
            {
              "grammaticalFeatures": [
                {
                  "text": "Transitive",
                  "type": "Subcategorization"
                },
                {
                  "text": "Present",
                  "type": "Tense"
                }
              ],
              "homographNumber": "002",
              "senses": [
                {
                  "definitions": [
                    "(in tennis and similar games) serve an ace against (an opponent)"
                  ],
                  "domains": [
                    "Tennis"
                  ],
                  "examples": [
                    {
                      "text": "he can ace opponents with serves of no more than 62 mph"
                    }
                  ],
                  "id": "m_en_gbus0005680.020",
                  "registers": [
                    "informal"
                  ],
                  "subsenses": [
                    {
                      "definitions": [
                        "score an ace on (a hole) or with (a shot)"
                      ],
                      "domains": [
                        "Golf"
                      ],
                      "examples": [
                        {
                          "text": "there was a prize for the first player to ace the hole"
                        }
                      ],
                      "id": "m_en_gbus0005680.026"
                    }
                  ]
                },
                {
                  "definitions": [
                    "achieve high marks in (a test or exam)"
                  ],
                  "examples": [
                    {
                      "text": "I aced my grammar test"
                    }
                  ],
                  "id": "m_en_gbus0005680.028",
                  "regions": [
                    "North American"
                  ],
                  "registers": [
                    "informal"
                  ],
                  "subsenses": [
                    {
                      "definitions": [
                        "outdo someone in a competitive situation"
                      ],
                      "examples": [
                        {
                          "text": "the magazine won an award, acing out its rivals"
                        }
                      ],
                      "id": "m_en_gbus0005680.029",
                      "notes": [
                        {
                          "text": "\"ace someone out\"",
                          "type": "wordFormNote"
                        }
                      ]
                    }
                  ]
                }
              ]
            }
          ],
          "language": "en",
          "lexicalCategory": "Verb",
          "pronunciations": [
            {
              "audioFile": "http://audio.oxforddictionaries.com/en/mp3/ace_gb_1.mp3",
              "dialects": [
                "British English"
              ],
              "phoneticNotation": "IPA",
              "phoneticSpelling": "eɪs"
            }
          ],
          "text": "ace"
        }
      ],
      "type": "headword",
      "word": "ace"
    }
  ]
}
