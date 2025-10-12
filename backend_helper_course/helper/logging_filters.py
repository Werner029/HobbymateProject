import logging
import re
from typing import Iterable


class TrimBodyFilter(logging.Filter):
    def __init__(self, max_length=2000):
        super().__init__()
        self.max_length = max_length

    def filter(self, record):
        if isinstance(record.args, tuple):
            record.args = tuple(
                (str(a)[: self.max_length] if i == 2 else a)
                for i, a in enumerate(record.args)
            )
        return True


DEFAULT_SECRET_KEYS = {
    'password',
    'passwd',
    'pwd',
    'token',
    'access_token',
    'refresh_token',
    'secret',
    'api_key',
    'authorization',
}


class MaskSecretsFilter(logging.Filter):
    def __init__(
        self,
        secrets: Iterable[str] | None = None,
        mask: str = '******',
        max_len: int | None = None,
    ):
        super().__init__()
        self.secrets = {s.lower() for s in (secrets or DEFAULT_SECRET_KEYS)}
        self.mask = mask
        self.max_len = max_len

        escaped = '|'.join(map(re.escape, self.secrets))
        self._pair_re = re.compile(
            rf'("?(?:{escaped})"?\s*[:=]\s*)["\"]?[^"\",\s]+["\"]?',
            re.I,
        )

    def _mask_str(self, text: str) -> str:
        text = self._pair_re.sub(r'\1' + self.mask, text)
        if self.max_len and len(text) > self.max_len:
            text = text[: self.max_len] + '…'  # pragma: no cover
        return text

    def _mask_obj(self, obj):
        if isinstance(obj, dict):
            return {  # pragma: no cover
                k: (
                    self.mask
                    if k.lower() in self.secrets
                    else self._mask_obj(v)
                )
                for k, v in obj.items()
            }  # pragma: no cover
        elif isinstance(obj, (list, tuple)):
            return type(obj)(
                self._mask_obj(v) for v in obj
            )  # pragma: no cover
        elif isinstance(obj, str):
            return self._mask_str(obj)
        return obj

    def filter(self, record: logging.LogRecord):
        if isinstance(record.msg, str):
            record.msg = self._mask_str(record.msg)
        if record.args:
            record.args = tuple(self._mask_obj(a) for a in record.args)
        if hasattr(record, 'extra') and isinstance(record.extra, dict):
            record.extra = self._mask_obj(record.extra)  # pragma: no cover

        return True
