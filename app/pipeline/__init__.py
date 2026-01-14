"""
Pipeline模块初始化
"""
from .risk_identification import RiskIdentificationPipeline
from .data_acquisition import DataAcquisitionPipeline

__all__ = ['RiskIdentificationPipeline', 'DataAcquisitionPipeline']
