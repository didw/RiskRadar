"""Kafka integration module"""
from .consumer import MLConsumer, MockKafkaConsumer
from .producer import MLProducer, MockKafkaProducer
from .schemas import RawNewsModel, EnrichedNewsModel, NLPResult, Entity, Sentiment, Keyword

__all__ = [
    'MLConsumer', 'MockKafkaConsumer',
    'MLProducer', 'MockKafkaProducer',
    'RawNewsModel', 'EnrichedNewsModel', 'NLPResult',
    'Entity', 'Sentiment', 'Keyword'
]