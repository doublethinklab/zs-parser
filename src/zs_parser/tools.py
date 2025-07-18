from datetime import datetime
from typing import Dict, List
from jsonpath_ng.ext import parse
import click


def remove_duplicates_by_key(json_list, key):
    seen = set()
    result = []
    for item in json_list:
        value = item.get(key)
        if value not in seen:
            seen.add(value)
            result.append(item)
    return result

def fb_parser(lst: List[Dict]) -> List[Dict]:
    result_data = []
    for x in lst:
        data = x.get('data', [])
        post_id = data.get('post_id')
        post_url = extract_json_path(data, '$..wwwURL')
        creation_time = datetime.fromtimestamp(min(extract_json_path(data, '$..story.creation_time'))).strftime("%Y-%m-%d %H:%M:%S")
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
        comment_count = extract_json_path(data, "$..comments_count_summary_renderer.feedback.comment_rendering_instance.comments.total_count")
        share_count = int(extract_json_path(data, '$..i18n_share_count')[0])
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
    click.echo(f"Data count: {len(result_data)}", err=True)
    result_data_ = remove_duplicates_by_key(result_data, 'post_id')
    click.echo(f"Data count: {len(result_data_)}", err=True)
    return result_data_





def extract_json_path(data: Dict, path: str) -> List:
    json_path = parse(path)
    m = json_path.find(data)
    return [match.value for match in m]