# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: cjedb.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0b\x63jedb.proto\x12\x05\x63jedb\"(\n\x08\x44\x61tabase\x12\x1c\n\x06\x65vents\x18\x01 \x03(\x0b\x32\x0c.cjedb.Event\"z\n\x05\x45vent\x12\x10\n\x08story_id\x18\x01 \x01(\x05\x12\x12\n\nstory_name\x18\x03 \x01(\t\x12$\n\x07\x63hoices\x18\x02 \x03(\x0b\x32\x13.cjedb.Event.Choice\x1a%\n\x06\x43hoice\x12\r\n\x05title\x18\x01 \x01(\t\x12\x0c\n\x04text\x18\x02 \x01(\t')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'cjedb_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _DATABASE._serialized_start=22
  _DATABASE._serialized_end=62
  _EVENT._serialized_start=64
  _EVENT._serialized_end=186
  _EVENT_CHOICE._serialized_start=149
  _EVENT_CHOICE._serialized_end=186
# @@protoc_insertion_point(module_scope)
