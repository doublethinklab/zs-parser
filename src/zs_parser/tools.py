from datetime import datetime
from typing import Dict, List
from jsonpath_ng.ext import parse
import click
import csv
import io


def safe_int(val):
    if isinstance(val, str):
        val = val.replace(',', '')
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def remove_duplicates_by_key(json_list, key):
    seen = set()
    result = []
    for item in json_list:
        value = item.get(key)
        if value not in seen:
            seen.add(value)
            result.append(item)
    return result

def tk_parser(lst: List[Dict]) -> List[Dict]:
    result_data = []
    for x in lst:
        data = x.get('data', {})
        
        post_id = data.get('id')
        post_url = x.get('source_platform_url')
        creation_time = datetime.fromtimestamp(data.get('createTime', 0)).strftime("%Y-%m-%d %H:%M:%S")
        
        attachments = []
        if data.get('video', {}).get('playAddr'):
            attachments.append(data['video']['playAddr'])
        if data.get('video', {}).get('cover'):
            attachments.append(data['video']['cover'])
        
        text = data.get('desc', '')
        
        author_info = data.get('author', {})
        author_name = author_info.get('nickname', '')
        author_id = author_info.get('uniqueId', '')
        
        stats = data.get('stats', {})
        like_count = safe_int(stats.get('diggCount', 0))
        comment_count = safe_int(stats.get('commentCount', 0))
        share_count = safe_int(stats.get('shareCount', 0))
        play_count = safe_int(stats.get('playCount', 0))
        
        result_data.append({
            "post_id": post_id,
            "post_url": post_url,
            "creation_time": creation_time,
            "attachments": attachments,
            "text": text,
            "author_name": author_name,
            "author_id": author_id,
            "like_count": like_count,
            "comment_count": comment_count,
            "share_count": share_count,
            "play_count": play_count
        })
    
    click.echo(f"Original Data count: {len(result_data)}", err=True)
    result_data_ = remove_duplicates_by_key(result_data, 'post_id')
    click.echo(f"Deduplicated Data count: {len(result_data_)}", err=True)
    return result_data_


def fb_parser(lst: List[Dict]) -> List[Dict]:
    result_data = []
    for x in lst:
        data = x.get('data', {})
        post_url = list(dict.fromkeys([url for url in deep_find(data, 'wwwURL') if url]))

        creation_times = [time for time in deep_find_path(data, 'story', ['creation_time']) if safe_int(time)]
        if creation_times:
            creation_time = datetime.fromtimestamp(min([safe_int(time) for time in creation_times])).strftime("%Y-%m-%d %H:%M:%S")
        else:
            creation_time = "Unknown"

        attachment_urls = []
        for attachments_of in deep_find(data, 'attachments'):
            attachment_urls += deep_find(attachments_of, 'url')
        attachments = list(dict.fromkeys([url for url in attachment_urls if url]))

        text_list = walk_path(data.get('comet_sections'), ['content', 'story', 'message', 'text'])
        if text_list:
            text = text_list[0]
        else:
            text = ""

        reaction_counts = [edges for edges in deep_find_path(
            data, 'comet_ufi_summary_and_actions_renderer', ['feedback', 'top_reactions', 'edges']
        ) if isinstance(edges, list)]
        if reaction_counts:
            reactions = [{i['node']['localized_name']: safe_int(i['reaction_count'])} for i in reaction_counts[0]]
            total_reaction_count = sum([safe_int(i['reaction_count']) for i in reaction_counts[0]])
        else:
            reactions = []
            total_reaction_count = 0

        comment_count_results = deep_find_path(
            data, 'comments_count_summary_renderer',
            ['feedback', 'comment_rendering_instance', 'comments', 'total_count']
        )
        comment_count = safe_int(comment_count_results[0]) if comment_count_results else 0

        share_count_results = deep_find(data, 'i18n_share_count')
        share_count = safe_int(share_count_results[0]) if share_count_results else 0
        result_data.append(
            {
                "post_id": facebook_post_id(x, data),
                "post_url": post_url,
                "creation_time": creation_time,
                "attachments": attachments,
                "text": text,
                "total_reaction_count": total_reaction_count,
                "reactions": reactions,
                "comment_count": comment_count,
                "share_count": share_count
            }
        )
    click.echo(f"Original Data count: {len(result_data)}", err=True)
    result_data_ = remove_duplicates_by_key(result_data, 'post_id')
    click.echo(f"Deduplicated Data count: {len(result_data_)}", err=True)
    return result_data_


def walk_path(value, path: List[str]) -> List:
    """Follow a path of keys, traversing any lists encountered along the way."""
    current = [value]
    for key in path:
        next_values = []
        for item in current:
            if isinstance(item, list):
                for entry in item:
                    if isinstance(entry, dict) and entry.get(key) is not None:
                        next_values.append(entry[key])
            elif isinstance(item, dict) and item.get(key) is not None:
                next_values.append(item[key])
        current = next_values
    return current


def deep_find(obj, key: str) -> List:
    """Collect all values of a key, anywhere in a nested object or list."""
    results = []

    def search(value):
        if isinstance(value, list):
            for item in value:
                search(item)
        elif isinstance(value, dict):
            for item_key, item_value in value.items():
                if item_key == key:
                    results.append(item_value)
                search(item_value)

    search(obj)
    return results


def deep_find_path(obj, key: str, path: List[str]) -> List:
    """Collect all values matching `$..key.rest.of.path`."""
    results = []
    for match in deep_find(obj, key):
        results += walk_path(match, path)
    return results


def facebook_post_id(item: Dict, data: Dict) -> str:
    """Determine the post ID of a Facebook item.

    Zeeschuimer's Facebook module stores the (base64-decoded) story ID, e.g.
    'Story:12345' or 'S:_I67890:12345'; the numerical post ID is the last
    segment. If the captured data has an explicit post_id, that is used.
    """
    if data.get('post_id'):
        return str(data['post_id'])

    post_id = str(item.get('item_id') or data.get('id') or '')
    if ':' in post_id:
        post_id = post_id.split(':')[-1]
    return post_id


def twitter_tweet(data: Dict) -> Dict:
    """Get a tweet's own fields.

    Zeeshuimer's X/Twitter module stores tweets in two shapes: the one the
    site's GraphQL API returns, where the tweet itself is under 'legacy', and
    the one the older adaptive.json endpoint returns, which the module
    rearranges into the same shape.
    """
    if isinstance(data.get('legacy'), dict):
        return data['legacy']
    if isinstance(data.get('tweet'), dict) and isinstance(data['tweet'].get('legacy'), dict):
        return data['tweet']['legacy']
    return {}


def twitter_author(data: Dict) -> Dict:
    """Get who posted a tweet.

    The author is in a different place depending on how old the captured data
    is; the current shape keeps it under 'core', older ones under 'legacy', and
    adaptive.json items have it added by the module.
    """
    candidates = (
        walk_path(data, ['core', 'user_results', 'result', 'core'])
        + walk_path(data, ['core', 'user_results', 'result', 'legacy'])
        + walk_path(data, ['tweet', 'core', 'user_results', 'result', 'core'])
        + walk_path(data, ['tweet', 'core', 'user_results', 'result', 'legacy'])
        + walk_path(data, ['user'])
    )

    for user in candidates:
        if isinstance(user, dict) and (user.get('screen_name') or user.get('name')):
            return {'name': user.get('name') or '', 'handle': user.get('screen_name') or ''}

    handles = [handle for handle in deep_find(data, 'screen_name') if isinstance(handle, str)]
    return {'name': '', 'handle': handles[0] if handles else ''}


def twitter_attachments(tweet: Dict) -> List[str]:
    """Collect the media attached to a tweet.

    For videos the highest quality variant is used, for images the image
    itself; 'extended_entities' is preferred because it holds all media of a
    tweet with several images, where 'entities' only holds the first.
    """
    media = []
    for source in (tweet.get('extended_entities'), tweet.get('entities')):
        if isinstance(source, dict) and isinstance(source.get('media'), list):
            media += source['media']

    urls = []
    for item in media:
        if not isinstance(item, dict):
            continue

        video_info = item.get('video_info')
        variants = []
        if isinstance(video_info, dict) and isinstance(video_info.get('variants'), list):
            variants = [v for v in video_info['variants']
                        if isinstance(v, dict) and v.get('url') and v.get('bitrate') is not None]

        if variants:
            variants.sort(key=lambda variant: safe_int(variant.get('bitrate')), reverse=True)
            urls.append(variants[0]['url'])
        elif item.get('media_url_https') or item.get('media_url'):
            urls.append(item.get('media_url_https') or item.get('media_url'))

    return list(dict.fromkeys(urls))


def tw_parser(lst: List[Dict]) -> List[Dict]:
    result_data = []
    for x in lst:
        data = x.get('data', {})
        tweet = twitter_tweet(data)
        author = twitter_author(data)

        post_id = str(tweet.get('id_str') or data.get('rest_id') or data.get('id') or '')

        # a retweet's own text is cut off after 140 characters, so the text and
        # media of the tweet that was retweeted are used instead
        retweets = [result for result in (
            walk_path(tweet, ['retweeted_status_result', 'result'])
            + walk_path(tweet, ['retweeted_status_result', 'result', 'tweet'])
        ) if isinstance(result, dict)]
        retweet = retweets[0] if retweets else None
        retweeted_from = twitter_author(retweet)['handle'] if retweet else ''
        source = twitter_tweet(retweet) if retweet else tweet

        # tweets longer than 280 characters keep their full text here
        long_text = [text for text in (
            walk_path(retweet or data, ['note_tweet', 'note_tweet_results', 'result', 'text'])
            + walk_path(retweet or data, ['tweet', 'note_tweet', 'note_tweet_results', 'result', 'text'])
        ) if isinstance(text, str)]

        text = long_text[0] if long_text else (source.get('full_text') or source.get('text') or '')

        view_counts = walk_path(data, ['views', 'count']) + walk_path(data, ['tweet', 'views', 'count'])

        if post_id and author['handle']:
            post_url = f"https://x.com/{author['handle']}/status/{post_id}"
        elif post_id:
            post_url = f"https://x.com/i/status/{post_id}"
        else:
            post_url = x.get('source_platform_url')

        created_at = tweet.get('created_at')
        if created_at:
            try:
                creation_time = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y") \
                    .astimezone().strftime("%Y-%m-%d %H:%M:%S")
            except (TypeError, ValueError):
                creation_time = "Unknown"
        else:
            creation_time = "Unknown"

        result_data.append({
            "post_id": post_id,
            "post_url": post_url,
            "creation_time": creation_time,
            "attachments": twitter_attachments(source),
            "text": text,
            "author_name": author['name'],
            "author_id": author['handle'],
            "like_count": safe_int(tweet.get('favorite_count')),
            "retweet_count": safe_int(tweet.get('retweet_count')),
            "reply_count": safe_int(tweet.get('reply_count')),
            "quote_count": safe_int(tweet.get('quote_count')),
            "view_count": safe_int(view_counts[0]) if view_counts else 0,
            "retweeted_from": retweeted_from,
            "promoted": bool(data.get('promoted'))
        })

    click.echo(f"Original Data count: {len(result_data)}", err=True)
    result_data_ = remove_duplicates_by_key(result_data, 'post_id')
    click.echo(f"Deduplicated Data count: {len(result_data_)}", err=True)
    return result_data_


def largest_media(candidates) -> str:
    """Pick the largest of a set of Instagram-style media candidates."""
    usable = [candidate for candidate in (candidates or [])
              if isinstance(candidate, dict) and candidate.get('url')]
    if not usable:
        return ""

    usable.sort(key=lambda candidate: safe_int(candidate.get('width')) * safe_int(candidate.get('height')),
                reverse=True)
    return usable[0]['url']


def threads_attachments(post: Dict) -> List[str]:
    """Collect the media attached to a Threads post.

    A post holds either one image or video, or a carousel of them, in the same
    shape Instagram uses.
    """
    posts = [post] + (post.get('carousel_media') if isinstance(post.get('carousel_media'), list) else [])

    urls = []
    for item in posts:
        if not isinstance(item, dict):
            continue

        if isinstance(item.get('video_versions'), list) and item['video_versions']:
            urls.append(largest_media(item['video_versions']))
        elif isinstance(item.get('image_versions2'), dict):
            urls.append(largest_media(item['image_versions2'].get('candidates')))

    return list(dict.fromkeys([url for url in urls if url]))


def th_parser(lst: List[Dict]) -> List[Dict]:
    result_data = []
    for x in lst:
        post = x.get('data', {})
        app_info = post.get('text_post_app_info') or {}

        # a repost has no content of its own: its text, media and counts are
        # those of the post that was reposted, while the author stays whoever
        # reposted it, as with a retweet on X
        repost = app_info.get('reposted_post') if isinstance(app_info.get('reposted_post'), dict) else None
        source = repost or post
        source_app_info = source.get('text_post_app_info') or {}

        author = post.get('user') or {}
        source_author = source.get('user') or author
        code = source.get('code') or post.get('code') or ''

        caption = source.get('caption') or {}

        result_data.append({
            "post_id": str(post.get('pk') or post.get('id') or ''),
            "post_url": f"https://www.threads.com/@{source_author.get('username') or ''}/post/{code}"
                        if code else x.get('source_platform_url'),
            "creation_time": datetime.fromtimestamp(post['taken_at']).strftime("%Y-%m-%d %H:%M:%S")
                             if post.get('taken_at') else "Unknown",
            "attachments": threads_attachments(source),
            "text": caption.get('text') or '',
            "author_name": author.get('full_name') or '',
            "author_id": author.get('username') or '',
            "like_count": safe_int(source.get('like_count')),
            "reply_count": safe_int(source_app_info.get('direct_reply_count')),
            "repost_count": safe_int(source_app_info.get('repost_count')),
            "reposted_from": (source_author.get('username') or '') if repost else ''
        })

    click.echo(f"Original Data count: {len(result_data)}", err=True)
    result_data_ = remove_duplicates_by_key(result_data, 'post_id')
    click.echo(f"Deduplicated Data count: {len(result_data_)}", err=True)
    return result_data_


def general_parser(lst: List[Dict]) -> List[Dict]:
    if not lst:
        return []
    
    first_item = lst[0]
    source_platform = first_item.get('source_platform', '')
    
    if 'facebook' in source_platform.lower():
        click.echo(f"Using Facebook parser for platform: {source_platform}", err=True)
        return fb_parser(lst)
    elif 'tiktok' in source_platform.lower():
        click.echo(f"Using TikTok parser for platform: {source_platform}", err=True)
        return tk_parser(lst)
    elif 'twitter' in source_platform.lower() or 'x.com' in source_platform.lower():
        click.echo(f"Using X/Twitter parser for platform: {source_platform}", err=True)
        return tw_parser(lst)
    elif 'threads' in source_platform.lower():
        click.echo(f"Using Threads parser for platform: {source_platform}", err=True)
        return th_parser(lst)
    else:
        click.echo(f"Unknown platform: {source_platform}, falling back to Facebook parser", err=True)
        return fb_parser(lst)


def extract_json_path(data: Dict, path: str) -> List:
    json_path = parse(path)
    m = json_path.find(data)
    return [match.value for match in m]


def write_csv_output(data: List[Dict], output_file: str = None) -> str:
    if not data:
        return ""
    
    output = io.StringIO()
    fieldnames = data[0].keys()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for row in data:
        flattened_row = {}
        for key, value in row.items():
            if isinstance(value, list):
                if key == 'attachments':
                    flattened_row[key] = '; '.join(str(v) for v in value)
                elif key == 'reactions':
                    reactions_str = '; '.join([f"{list(r.keys())[0]}:{list(r.values())[0]}" for r in value]) if value else ""
                    flattened_row[key] = reactions_str
                else:
                    flattened_row[key] = '; '.join(str(v) for v in value)
            elif isinstance(value, bool):
                flattened_row[key] = "true" if value else "false"
            else:
                flattened_row[key] = str(value) if value is not None else ""
        writer.writerow(flattened_row)
    
    csv_content = output.getvalue()
    output.close()
    
    if output_file:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            f.write(csv_content)
    
    return csv_content