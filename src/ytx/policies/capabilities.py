READ_CHANNEL = "read:channel"
READ_VIDEO = "read:video"
READ_ANALYTICS = "read:analytics"
READ_REPORTING = "read:reporting"

COMMAND_CAPABILITIES = {
    "channel_get": READ_CHANNEL,
    "channel_videos": READ_VIDEO,
    "video_get": READ_VIDEO,
    "video_analytics": READ_ANALYTICS,
    "analytics_query": READ_ANALYTICS,
}
