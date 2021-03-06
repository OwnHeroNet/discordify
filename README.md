[![Board Status](https://dev.azure.com/OwnHeroNet/d4eb3e12-4416-419f-a0b7-f9f23a7a23c9/7f9cf3b5-0b49-4fc9-a104-a88d75cd84fd/_apis/work/boardbadge/c4004b67-7174-4b36-9a84-43e3f522d9ca)](https://dev.azure.com/OwnHeroNet/d4eb3e12-4416-419f-a0b7-f9f23a7a23c9/_boards/board/t/7f9cf3b5-0b49-4fc9-a104-a88d75cd84fd/Microsoft.RequirementCategory/)

# ![Logo](logo/Logo%20Dark%20Font.png)

Discordify is a wrapper to execute UNIX shell commands and notify a channel in either Slack or Discord about the results.

![Demo](screenshots/demo.gif)

#### Project Status

[![Build Status](https://travis-ci.com/OwnHeroNet/discordify.svg?branch=master)](https://travis-ci.com/OwnHeroNet/discordify)

### Installation

1. Install this package using pip:
    `pip install git+https://github.com/OwnHeroNet/discordify`
2. Set up an alias: `alias discordify="python3 -m discordify"`
3. Add a config for a specific webhook to the global or local config (see below).

### Usage

```bash
# wrap my_tool executable in discordiy
discordify my_tool

# wrap my_tool executable in discordiy
discordify my_tool | tee -f log

# this also supports pipes
cat /tmp/socket | discordify process_input >/var/log/something
```

### Configuration file

The configuration stack is evaluated as follows:

- Global: `/etc/discordify.conf`
- Local: `${HOME}/.discordify.conf`
- Instance: command line opts

All configuration options are optional, _except_ for webhook.

The configuration file format is `JSON` and comes with the following parameters.
If the `user_email` is set, but `user_icon` isn't, we infer a gravatar link
automatically. The default thumbnail icon is the Discordify logo.

The footer usually contains "via `$HOSTNAME`".

Default color is solarized red.

```json
{
    "user_name": "Your Name",
    "user_email": "Your Email Address",
    "user_url": "Your Website Address",
    "thumbnail": "https://path.to.your/image.png",
    "color": "0xD11C24",
    "title": "Discordify Notification",
    "webhook": "https://discordapp.com/api/webhooks/id/token"
}
```

For a full list of supported options see `discordify --help`.

### Getting the webhook url

Below you see the user interface for adding webhooks in Discord.
Either go to [Server Settings] -> [Webhooks] -> [Create Webhook] and configure a new webhook or go to
[Edit Channel] -> [Webhooks] -> [Create Webhook].

![WebHook UI in Discord](screenshots/webhook_generation_discord_1.png)

![WebHook UI in Discord](screenshots/webhook_generation_discord_2.png)

![WebHook UI in Discord](screenshots/webhook_generation_discord_3.png)

Copy the webhook URL and paste it in your Discordify configuration file or use it on the commandline
as `discordify --webhook 'https://your-webhook.example'`.
