from color import header
header("Structured Output example", "yellow")

import sys
import os
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

from langchain_openai import AzureChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv
import json
import yaml

load_dotenv()

# Azure OpenAI setup
llm = AzureChatOpenAI(
    azure_deployment = os.getenv("AZURE_OPENAI_API_DEPLOYMENT"),
    api_version      = os.getenv("AZURE_OPENAI_API_VERSION"),
    api_key          = os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint   = os.getenv("AZURE_OPENAI_ENDPOINT"),
    max_tokens       = 1500,
    temperature      = 0,
    verbose          = False,
    seed             = 1234
)

header("[Structure output] Movie information in three formats: JSON, YAML, Markdown")

# Movie data structure
class Movie(BaseModel):
    title: str = Field(description="Movie title")
    director: str = Field(description="Director")
    year: int = Field(description="Release year")
    genre: List[str] = Field(description="Movie genres")
    rating: float = Field(description="Rating from 1.0 to 10.0")
    duration_minutes: int = Field(description="Duration in minutes")
    cast: List[str] = Field(description="Main actors")
    plot_summary: str = Field(description="Brief plot description")
    budget_millions: Optional[float] = Field(description="Budget in millions of dollars", default=None)
    box_office_millions: Optional[float] = Field(description="Box office in millions of dollars", default=None)

def extract_movie_info(text: str) -> Movie:
    """Extracts movie information from text"""
    
    parser = PydanticOutputParser(pydantic_object=Movie)
    
    prompt = PromptTemplate(
        template="""Extract movie information from the following text and return in specified format.
If some information is missing, try to give reasonable assumptions based on context.

{format_instructions}

Movie text: {text}

Result:""",
        input_variables=["text"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    formatted_prompt = prompt.format(text=text)
    response = llm.invoke(formatted_prompt)
    
    try:
        return parser.parse(response.content)
    except Exception as e:
        print(f"Parsing error: {e}")
        return None

# Parsers for different output formats

class JSONParser(BaseOutputParser):
    """Parser for JSON output"""
    
    def parse(self, text: str) -> dict:
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = text[start:end]
                return json.loads(json_str)
            else:
                raise ValueError("JSON not found in text")
        except Exception as e:
            raise ValueError(f"JSON parsing error: {e}")

class YAMLParser(BaseOutputParser):
    """Parser for YAML output"""
    
    def parse(self, text: str) -> dict:
        try:
            # Remove markdown blocks and extra symbols
            text = text.replace('```yaml', '').replace('```', '').strip()
            
            # Search for YAML block line by line
            lines = text.split('\n')
            yaml_lines = []
            
            for line in lines:
                # Skip empty lines at the beginning
                if not yaml_lines and not line.strip():
                    continue
                    
                # Add lines that look like YAML
                if line.strip() and (
                    ':' in line or 
                    line.strip().startswith('-') or
                    line.startswith('  ') or
                    line.startswith('    ')
                ):
                    yaml_lines.append(line)
                elif yaml_lines:  # If we already started collecting YAML and met non-YAML line
                    break
            
            yaml_text = '\n'.join(yaml_lines)
            return yaml.safe_load(yaml_text)
        except Exception as e:
            raise ValueError(f"YAML parsing error: {e}")

class MarkdownParser(BaseOutputParser):
    """Parser for Markdown format text"""
    
    def parse(self, text: str) -> str:
        # Return text as is, since Markdown is a text format
        return text.strip()

def get_movie_info_json(text: str) -> dict:
    """Gets movie information in JSON format"""
    
    parser = JSONParser()
    
    prompt = PromptTemplate(
        template="""Extract movie information from text and return in beautiful JSON format:

{{
    "title": "movie title",
    "director": "director",
    "year": release_year,
    "genre": ["genre1", "genre2"],
    "rating": rating_from_1_to_10,
    "duration_minutes": duration_in_minutes,
    "cast": ["actor1", "actor2", "actor3"],
    "plot_summary": "brief plot description",
    "budget_millions": budget_in_millions_of_dollars,
    "box_office_millions": box_office_in_millions_of_dollars
}}

Text: {text}

JSON:""",
        input_variables=["text"]
    )
    
    formatted_prompt = prompt.format(text=text)
    response = llm.invoke(formatted_prompt)
    
    try:
        return parser.parse(response.content)
    except Exception as e:
        print(f"Ошибка JSON: {e}")
        return None

def get_movie_info_yaml(text: str) -> dict:
    """Gets movie information in YAML format"""
    
    parser = YAMLParser()
    
    prompt = PromptTemplate(
        template="""Extract movie information from text and return in YAML format:

title: movie title
director: director
year: release_year
genre:
  - genre1
  - genre2
rating: rating_from_1_to_10
duration_minutes: duration_in_minutes
cast:
  - actor1
  - actor2
  - actor3
plot_summary: brief plot description
budget_millions: budget_in_millions_of_dollars
box_office_millions: box_office_in_millions_of_dollars

Text: {text}

YAML:""",
        input_variables=["text"]
    )
    
    formatted_prompt = prompt.format(text=text)
    response = llm.invoke(formatted_prompt)
    
    try:
        return parser.parse(response.content)
    except Exception as e:
        print(f"YAML error: {e}")
        return None

def get_movie_info_markdown(text: str) -> str:
    """Gets movie information in Markdown format"""
    
    parser = MarkdownParser()
    
    prompt = PromptTemplate(
        template="""Extract movie information from text and format in beautiful Markdown:

# Movie Title

## Basic Information
- **Director:** director name
- **Release Year:** year
- **Genre:** genre1, genre2
- **Rating:** ⭐ X.X/10
- **Duration:** XXX minutes

## Cast
- Actor 1
- Actor 2 
- Actor 3

## Plot
Brief description of the movie plot...

## Commercial Success
- **Budget:** $XXX million
- **Box Office:** $XXX million

Text: {text}

Markdown:""",
        input_variables=["text"]
    )
    
    formatted_prompt = prompt.format(text=text)
    response = llm.invoke(formatted_prompt)
    
    return parser.parse(response.content)

# Demonstration of all formats
movie_text = """
The movie 'Inception' is a 2010 science fiction thriller directed by Christopher Nolan.
It stars Leonardo DiCaprio, Marion Cotillard, Tom Hardy, and Elliot Page.
The movie tells the story of a team of thieves who penetrate people's subconscious through their dreams
to steal secrets or implant ideas. The film has a runtime of 148 minutes.
The movie's budget was around 160 million dollars, and worldwide box office reached 836 million.
The film received numerous awards and has a rating of 8.8 on IMDb.
"""

header("Original movie text")
print(movie_text.strip())

header("PYDANTIC MODEL - Strict typing")

pydantic_result = extract_movie_info(movie_text)
if pydantic_result:
    print(f"Title: {pydantic_result.title}")
    print(f"Director: {pydantic_result.director}")
    print(f"Year: {pydantic_result.year}")
    print(f"Genres: {', '.join(pydantic_result.genre)}")
    print(f"Rating: {pydantic_result.rating}/10")
    print(f"Duration: {pydantic_result.duration_minutes} minutes")
    print(f"Cast: {', '.join(pydantic_result.cast)}")
    print(f"Budget: ${pydantic_result.budget_millions} million")
    print(f"Box Office: ${pydantic_result.box_office_millions} million")

header("JSON PRETTY PRINT - Beautiful JSON")

json_result = get_movie_info_json(movie_text)
if json_result:
    print(json.dumps(json_result, ensure_ascii=False, indent=2))

header("YAML FORMAT - Human-readable YAML")

yaml_result = get_movie_info_yaml(movie_text)
if yaml_result:
    print(yaml.dump(yaml_result, allow_unicode=True, default_flow_style=False, indent=2))

header("MARKDOWN FORMAT - Beautiful formatting")

markdown_result = get_movie_info_markdown(movie_text)
if markdown_result:
    print(markdown_result)

header("Demonstration completed!")
