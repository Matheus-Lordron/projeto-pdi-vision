from .color import GrayscaleFilter, ChannelExtractionFilter

FILTER_REGISTRY = {
    "Cores e Canais": [
        GrayscaleFilter,
        ChannelExtractionFilter
    ]
}