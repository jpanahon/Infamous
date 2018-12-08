import datetime
import discord


embed_color = 0x0f0f0f


def time_(time):
    delta_uptime = datetime.datetime.utcnow() - time
    hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    return days, hours, minutes, seconds


def status__(status_):
    status = None
    se = None
    if status_ == 'online':
        status = 'Online'
        se = '<:online:435402249448062977> '

    elif status_ == 'offline':
        status = 'Offline'
        se = '<:offline:435402248282046464>'

    elif status_ == 'away':
        status = 'Away'
        se = '<:away:435402245144576000> '

    elif status_ == 'dnd':
        status = 'Do Not Disturb'
        se = '<:dnd:435402246738673675>'

    return status, se


def activity(activity_):
    if activity_:
        activity_status = None
        if activity_.type.name == "playing":
            activity_status = "Playing <:controller:444678089415458828>"

        elif activity_.type.name == "watching":
            activity_status = "Watching <:YouTube:444677705254961152>"

        elif activity_.type.name == "listening":
            activity_status = "Listening <:SpotifyLogo:444677360395223043>"

        elif activity_.type.name == "streaming":
            activity_status = "Streaming <:twitchlogo:444676989681532929>"

        return activity_status


def ud_embed(definition_, current, max_):
    embed = discord.Embed(color=embed_color)
    embed.set_author(name=definition_['word'], url=definition_['permalink'])
    embed.description = ((definition_['definition'])[:2046] + '..') if len(definition_['definition']) > 2048 \
        else definition_['definition']
    embed.add_field(name="Example:",
                    value=((definition_['example'])[:1022] + '..') if len(definition_['example']) > 1024
                    else definition_['example'])
    embed.set_footer(text=f"Written by: {definition_['author']} | Entry {current} of {max_}")

    embed.set_thumbnail(
        url=
        "http://a2.mzstatic.com/us/r30/Purple/v4/dd/ef/75/ddef75c7-d26c-ce82-4e3c-9b07ff0871a5/mzl.yvlduoxl.png"
    )
    return embed
