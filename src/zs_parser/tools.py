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
        post_id = data.get('post_id')
        post_url = extract_json_path(data, '$..wwwURL')
        creation_times = extract_json_path(data, '$..story.creation_time')
        if creation_times:
            creation_time = datetime.fromtimestamp(min(creation_times)).strftime("%Y-%m-%d %H:%M:%S")
        else:
            creation_time = "Unknown"
        attachments = list(set(extract_json_path(data, '$..attachments..url')))  # attachments..uri

        text = extract_json_path(data, "comet_sections.content.story.message.text")
        # comet_sections.content.story.message.text

        reaction_counts = extract_json_path(data, '$..comet_ufi_summary_and_actions_renderer.feedback.top_reactions.edges')
        if reaction_counts:
            reactions = [{i['node']['localized_name']: i['reaction_count']} for i in reaction_counts[0]]
            total_reaction_count = sum([i['reaction_count'] for i in reaction_counts[0]])
        else:
            reactions = []
            total_reaction_count = 0
        comment_count_results = extract_json_path(data, "$..comments_count_summary_renderer.feedback.comment_rendering_instance.comments.total_count")
        comment_count = comment_count_results[0] if comment_count_results else 0
        
        share_count_results = extract_json_path(data, '$..i18n_share_count')
        share_count = safe_int(share_count_results[0]) if share_count_results else 0
        result_data.append(
            {
                "post_id": post_id,
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
            else:
                flattened_row[key] = str(value) if value is not None else ""
        writer.writerow(flattened_row)
    
    csv_content = output.getvalue()
    output.close()
    
    if output_file:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            f.write(csv_content)
    
    return csv_content