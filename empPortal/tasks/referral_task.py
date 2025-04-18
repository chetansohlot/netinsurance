from ..models import UploadedZip, FileAnalysis, ExtractedFile, BulkPolicyLog, Commission, PolicyDocument, UnprocessedPolicyFiles, ChatGPTLog, UploadedExcel
from ..models import PolicyInfo, PolicyVehicleInfo, AgentPaymentDetails, InsurerPaymentDetails, FranchisePayment
from ..models import FranchisePaymentLog, PolicyInfoLog, PolicyVehicleInfoLog, AgentPaymentDetailsLog, InsurerPaymentDetailsLog
import django, dramatiq, fitz, os, zipfile, requests, re, json, traceback, time, logging, shutil
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import now
from django_q.tasks import async_task
OPENAI_API_KEY = settings.OPENAI_API_KEY
from django.db.models import F
from ..utils import getUserNameByUserId, commisionRateByMemberId, insurercommisionRateByMemberId, to_int
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import filepath_to_uri
import pandas as pd



