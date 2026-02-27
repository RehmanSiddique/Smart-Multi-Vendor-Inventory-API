"""
Patch to fix DRF format suffix converter registration issue.
"""

from django.urls import converters
from rest_framework.urlpatterns import _get_path_converters, _DEFAULT_FORMAT_SUFFIX_KWARG


def patched_format_suffix_patterns(urlpatterns, suffix_required=False, allowed=None):
    """
    Patch for format_suffix_patterns that checks if converter is already registered.
    """
    from django.urls.resolvers import URLPattern
    from django.urls.resolvers import RoutePattern
    from django.urls.resolvers import URLResolver
    from django.core.exceptions import ImproperlyConfigured
    
    # Get or create the converter
    converter_name = 'drf_format_suffix'
    
    # Check if already registered
    if converter_name not in converters.converters:
        from rest_framework.urlpatterns import _FormatSuffixConverter
        converters.register_converter(_FormatSuffixConverter, converter_name)
    
    # Rest of the original function
    from rest_framework.urlpatterns import _FormatSuffixPattern, _FormatSuffixResolver
    from rest_framework.urlpatterns import _get_path_converters
    
    new_patterns = []
    for pattern in urlpatterns:
        if isinstance(pattern, URLResolver):
            # Recursively process resolvers
            new_patterns.append(
                URLResolver(
                    pattern.pattern,
                    patched_format_suffix_patterns(
                        pattern.url_patterns,
                        suffix_required=suffix_required,
                        allowed=allowed
                    ),
                    pattern.default_kwargs,
                    pattern.app_name,
                    pattern.namespace
                )
            )
        elif isinstance(pattern, URLPattern):
            # Process individual patterns
            callback = pattern.callback
            converters = _get_path_converters(pattern.pattern)
            
            if converters and converters[-1] == converter_name:
                # This pattern already has the suffix converter
                new_patterns.append(pattern)
            else:
                # Add the suffix converter
                new_patterns.append(
                    _FormatSuffixPattern(pattern, suffix_required, allowed)
                )
        else:
            new_patterns.append(pattern)
    
    return new_patterns


# Monkey patch DRF
import rest_framework.urlpatterns
rest_framework.urlpatterns.format_suffix_patterns = patched_format_suffix_patterns