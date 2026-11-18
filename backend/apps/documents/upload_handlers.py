"""Bounded multipart upload guard preventing excessive temp-disk spooling."""
from contextlib import suppress

from django.core.files.uploadhandler import FileUploadHandler
from rest_framework.exceptions import ValidationError

MAX_UPLOAD_FILE_BYTES = 5 * 1024 * 1024
MAX_UPLOAD_FILES_COUNT = 10
MAX_UPLOAD_BATCH_BYTES = MAX_UPLOAD_FILE_BYTES * MAX_UPLOAD_FILES_COUNT
MAX_MULTIPART_OVERHEAD_BYTES = 256 * 1024


def close_open_handler_files(request):
    for handler in getattr(request, "upload_handlers", ()) or ():
        handle = getattr(handler, "file", None)
        if handle is not None:
            with suppress(OSError):
                handle.close()


class BoundedUploadGuardHandler(FileUploadHandler):
    """Abort oversized or overly large batch uploads before buffering chunks."""

    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
        max_total = MAX_UPLOAD_BATCH_BYTES + MAX_MULTIPART_OVERHEAD_BYTES
        if content_length is not None and content_length > max_total:
            raise ValidationError("Upload request exceeds maximum allowed batch size.")
        return None

    def upload_state(self):
        target = self.request if self.request is not None else self
        state = getattr(target, "_bounded_upload_state", None)
        if state is None:
            state = {"files": 0, "total_bytes": 0}
            setattr(target, "_bounded_upload_state", state)
        return state

    def new_file(self, field_name, file_name, content_type, content_length,
                 charset=None, content_type_extra=None):
        super().new_file(field_name, file_name, content_type, content_length,
                         charset, content_type_extra)
        state = self.upload_state()
        state["files"] += 1
        self._current_file_bytes = 0
        if state["files"] > MAX_UPLOAD_FILES_COUNT:
            close_open_handler_files(self.request)
            raise ValidationError("Upload batch cannot exceed 10 files.")
        if content_length is not None and content_length > MAX_UPLOAD_FILE_BYTES:
            close_open_handler_files(self.request)
            raise ValidationError("File size exceeds maximum allowed limit of 5 MB.")

    def receive_data_chunk(self, raw_data, start):
        state = self.upload_state()
        chunk_len = len(raw_data)
        self._current_file_bytes = getattr(self, "_current_file_bytes", 0) + chunk_len
        state["total_bytes"] += chunk_len
        if self._current_file_bytes > MAX_UPLOAD_FILE_BYTES:
            close_open_handler_files(self.request)
            raise ValidationError("File size exceeds maximum allowed limit of 5 MB.")
        if state["total_bytes"] > MAX_UPLOAD_BATCH_BYTES:
            close_open_handler_files(self.request)
            raise ValidationError("Upload request exceeds maximum allowed batch size.")
        return raw_data

    def file_complete(self, file_size):
        return None
