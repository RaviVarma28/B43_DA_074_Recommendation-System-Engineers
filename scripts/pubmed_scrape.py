import pandas as pd
from httpx import get
from selectolax.parser import HTMLParser


def get_articles(url=None, tot_pages=1) -> pd.DataFrame:
    
    """
    This fuctions takes in the url for PubMed articles section and Number of pages to scrape as inputs
    and outputs a DataFrame of the articles, its authors and links.
    """

    if url is None or tot_pages <0:
        raise Exception("Url or Total Number of pages are not specified")
    
    article_ids = []
    article_headings = []
    article_links = []
    article_authors = []
    article_tags = []
    article_years = []
    
    # This site follows simple pagination
    next_page=""
    pages = 1

    while pages <= tot_pages: 
        resp = get(url+next_page)
        tree = HTMLParser(resp.text)

        # Incase the request was blocked, this is exception is raised.
        if resp.status_code!=200:
            raise Exception("Oops! Something went wrong with the request.")

        ids = [id.attrs['data-article-id'] for id in tree.css("article .docsum-title")]
        headings = [id.text().strip() for id in tree.css("article .docsum-title")]
        links = [f"https://pubmed.ncbi.nlm.nih.gov{l.attrs['href']}" for l in tree.css("article .docsum-title")]
        authors = [a.text().split(", ") for a in tree.css("article .full-authors")]
        tags = [" ".join(t.text().split()[:-1]) for t in tree.css(".short-journal-citation")]
        years = [int("".join(t.text().split()[-1].replace(".",""))) for t in tree.css(".short-journal-citation")]

        # The following extends will add the articles, as that was easy with this type of pagination and extraction.
        article_ids.extend(ids)
        article_headings.extend(headings)
        article_links.extend(links)
        article_authors.extend(authors)
        article_tags.extend(tags)
        article_years.extend(years)

        pages += 1
        next_page=f"&page={pages}"

        # Logging ouput is added to show progress of scraping.
        print("Download Progress")
        if pages%5==0:
            print(f"{pages} pages scraped...")
    
    # Creating a DataFrame
    df = pd.DataFrame(
        {
            "ID": article_ids,
            "Article": article_headings,
            "Authors": article_authors,
            "Published_Year":article_years,
            "Tag": article_tags,
            "Link": article_links
        }
    )
    
    print("Scraping Complete!")

    return df


if __name__ == "__main__":
    url = "https://pubmed.ncbi.nlm.nih.gov/trending/?sort=date"
    n_pages = 100

    df = get_articles(url, n_pages)
    df.to_csv("data/pubmed.csv", index=False)