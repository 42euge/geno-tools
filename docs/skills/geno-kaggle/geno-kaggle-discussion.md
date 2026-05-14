---
title: geno-kaggle-discussion
description: "Kaggle Discussion Scraper"
---

# geno-kaggle-discussion

`/geno-kaggle-discussion`

> "Kaggle Discussion Scraper"

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` — Optional. Can be:
- (empty) — scrape all discussions and generate insights
- `scrape` — only scrape discussions, skip insight generation
- `insights` — only regenerate insights from existing YAML files
- A track name (e.g., `learning`, `metacognition`) — regenerate insights for one track

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Output Location

All output goes under:
```
competition-info/kaggle-discussions/
├── threads/                          # Individual thread YAML files
│   ├── 682012-welcome-to-measuring-progress.yaml
│   ├── 681731-kaggle-benchmarks-product-feedback.yaml
│   └── ...
├── index.yaml                        # Master index of all threads
└── insights/                         # Per-track insight summaries
    ├── learning.md
    ├── metacognition.md
    ├── attention.md
    ├── executive-functions.md
    ├── social-cognition.md
    └── general.md                    # Cross-track / competition-wide insights
```

## Workflow

### Step 1: Scrape all discussion topics

Use the Kaggle Search API to fetch all discussion topics for the competition:

```python
import requests, json

with open(os.path.expanduser('~/.kaggle/kaggle.json')) as f:
    creds = json.load(f)

session = requests.Session()
session.auth = (creds['username'], creds['key'])
session.headers.update({
    'Content-Type': 'application/json',
    'User-Agent': 'kaggle-api/v1.7.0'
})

# Fetch topics (DocumentType.TOPIC = 8)
all_topics = []
page_token = ''
while True:
    payload = {
        'filters': {
            'documentTypes': [8],
            'discussionFilters': {'sourceType': 1},  # COMPETITION
            'query': 'kaggle-measuring-agi',
        },
        'pageSize': 50,
    }
    if page_token:
        payload['pageToken'] = page_token

    resp = session.post(
        'https://api.kaggle.com/v1/search.SearchApiService/ListEntities',
        json=payload
    )
    data = resp.json()
    docs = data.get('documents', [])
    all_topics.extend(docs)
    page_token = data.get('nextPageToken', '')
    if not page_token or not docs:
        break
```

### Step 2: Scrape all comments

Fetch all comments using the same API with DocumentType.COMMENT = 6:

```python
all_comments = []
page_token = ''
while True:
    payload = {
        'filters': {
            'documentTypes': [6],
            'discussionFilters': {'sourceType': 1},
            'query': 'kaggle-measuring-agi',
        },
        'pageSize': 50,
    }
    if page_token:
        payload['pageToken'] = page_token

    resp = session.post(
        'https://api.kaggle.com/v1/search.SearchApiService/ListEntities',
        json=payload
    )
    data = resp.json()
    docs = data.get('documents', [])
    all_comments.extend(docs)
    page_token = data.get('nextPageToken', '')
    if not page_token or not docs:
        break
```

### Step 3: For each topic, fetch its full thread via WebFetch

The Search API may not return all comments. For each topic, also fetch the full thread page to capture any missing comments:

```
https://www.kaggle.com/competitions/kaggle-measuring-agi/discussion/{topic_id}
```

Use `WebFetch` on each discussion URL with a prompt to extract ALL comments including author, date, content, and votes. Merge with API comments (deduplicate by comment ID from `newCommentUrl`).

### Step 4: Group comments by topic

Each comment's `discussionDocument.newCommentUrl` contains the parent topic ID:
```
/competitions/kaggle-measuring-agi/discussion/{topic_id}#{comment_id}
```

Extract the topic_id from the URL path and group comments under their parent topic.

### Step 5: Save each thread as YAML

For each topic, create a YAML file named `{topic_id}-{slugified-title}.yaml`:

```yaml
id: 682012
title: "Welcome to Measuring Progress Toward AGI - Cognitive Abilities"
url: "https://www.kaggle.com/competitions/kaggle-measuring-agi/discussion/682012"
author:
  username: "nicholaskanggoog"
  display_name: "Nicholas Kang"
  tier: "STAFF"
created: "2026-03-17T20:33:36Z"
updated: "2026-03-25T15:50:38Z"
votes: 12
tags: []  # inferred track tags, e.g. [metacognition, attention]

post:
  markdown: |
    Hi team,

    I'm Nick, Product Manager for Kaggle Benchmarks...
  stripped: "Hi team, I'm Nick..."

comments:
  - id: 3422608
    author:
      username: "someuser"
      display_name: "Some User"
      tier: "CONTRIBUTOR"
    created: "2026-03-18T10:00:00Z"
    votes: 2
    markdown: |
      Great initiative! Looking forward to this.
    stripped: "Great initiative! Looking forward to this."
  - id: 3422700
    # ... more comments
```

### Step 6: Auto-tag threads by track

Classify each thread into one or more tracks based on title and content analysis:

- **learning** — mentions learning, knowledge acquisition, few-shot, in-context learning, training data
- **metacognition** — mentions metacognition, calibration, confidence, self-awareness, knowing what it knows
- **attention** — mentions attention, focus, distraction, selective attention, filtering
- **executive-functions** — mentions planning, inhibition, cognitive flexibility, task switching, working memory
- **social-cognition** — mentions social cognition, theory of mind, empathy, social situations, perspective-taking
- **general** — competition logistics, SDK issues, getting started, feedback, rules

A thread can have multiple tags. Include the tags in both the YAML file and the index.

### Step 7: Build the master index

Create `index.yaml` with a summary of all threads:

```yaml
scraped_at: "2026-03-25T12:00:00Z"
competition: "kaggle-measuring-agi"
total_threads: 25
total_comments: 42

threads:
  - id: 682012
    title: "Welcome to Measuring Progress Toward AGI - Cognitive Abilities"
    author: "nicholaskanggoog"
    created: "2026-03-17T20:33:36Z"
    votes: 12
    comment_count: 7
    tags: [general]
    file: "682012-welcome-to-measuring-progress.yaml"
  # ... sorted by votes descending

by_track:
  learning:
    thread_count: 3
    threads: [681993, ...]
  metacognition:
    thread_count: 5
    threads: [682752, 682023, ...]
  attention:
    thread_count: 2
    threads: [683736, ...]
  executive-functions:
    thread_count: 2
    threads: [683411, ...]
  social-cognition:
    thread_count: 2
    threads: [684117, ...]
  general:
    thread_count: 15
    threads: [682012, 681731, ...]
```

### Step 8: Generate per-track insights

For each track, read all threads tagged with that track and generate an insight summary as a markdown file. Each insight file should include:

```markdown
# {Track Name} — Discussion Insights

*Generated: 2026-03-25 | Threads analyzed: N | Comments analyzed: N*

## Key Themes

1. **Theme name** — Brief description of the recurring theme
   - Supporting evidence from threads [link to thread YAML]

## Notable Benchmarks Shared

| Benchmark | Author | Key Finding | Thread |
|-----------|--------|-------------|--------|
| META-COG  | user   | AI scores 8.33% on self-awareness | 682752 |

## Community Concerns & Feedback

- Bullet points of concerns raised and any resolutions

## Ideas & Opportunities

- Ideas from discussions that could inform benchmark design

## Organizer Announcements

- Official announcements and clarifications relevant to this track

## Open Questions

- Unresolved questions from the community
```

For the `general.md` file, focus on:
- Competition logistics and rule changes
- SDK/platform issues and workarounds
- Cross-track observations
- Community sentiment and participation trends

### Step 9: Report results

Print a summary:
- Total threads scraped
- Total comments captured
- Threads per track
- Any threads that failed to scrape (with error details)
- Path to the output directory

## Important Notes

- **API endpoint**: `https://api.kaggle.com/v1/search.SearchApiService/ListEntities` (POST)
- **Auth**: Basic auth from `~/.kaggle/kaggle.json` (username + key)
- **Rate limiting**: Add a 1-second delay between WebFetch calls to avoid rate limiting
- **Idempotent**: If thread YAML files already exist, compare and update only if content has changed. Log which threads were new/updated/unchanged.
- **Comment ordering**: Sort comments by `created` timestamp (ascending) within each thread
- **YAML formatting**: Use block scalars (`|`) for markdown content to preserve formatting
- **Track classification**: Use the thread's title + post markdown + comment content for classification. Weight the title most heavily.
- **Parallel fetching**: Use up to 3 parallel Agents for WebFetch calls to speed up scraping, but respect rate limits.

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-kaggle-discussion \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```

- `success` = index.yaml written and at least one insight markdown generated
- `failure` = API scrape returned no threads, or YAML/insight generation failed
- `abandoned` = user stopped early

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-kaggle](index.md)
