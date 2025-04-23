from django_cron import CronJobBase, Schedule
from empPortal.models import PolicyDocument, FileAnalysis, ExtractedFile
from django_q.tasks import async_task
from django.utils import timezone

class ReprocessPoliciesCronJob(CronJobBase):
    RUN_EVERY_MINS = 2  # every 3 minutes

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'empPortal.reprocess_policies_cron'  # Unique code for the cron job

    def do(self):
        # Fetch all policies with status == 4
        policies_to_reprocess = PolicyDocument.objects.exclude(status=6)[:10]
        
        for policy in policies_to_reprocess:
            try:
                # You can use a more complex logic to get the file_obj or task as needed
                file_obj = ExtractedFile.objects.filter(policy_id=policy.id).last()
                print(file_obj.id)
                async_task('empPortal.tasks.upload_pdf_store_source_id', file_obj.id)

            except PolicyDocument.DoesNotExist:
                print(f"File with ID {policy.id} not found in PolicyDocument")
            
            except FileAnalysis.DoesNotExist:
                print(f"File with ID {policy.id} not found in FileAnalysis")
                
            except ExtractedFile.DoesNotExist:
                print(f"File with ID {policy.id} not found in ExtractedFile")
        
        print(f"Reprocessed policies with status 4 at {timezone.now()}")
