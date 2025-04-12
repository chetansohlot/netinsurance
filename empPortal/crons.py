from django_cron import CronJobBase, Schedule
from empPortal.models import PolicyDocument, FileAnalysis, ExtractedFile
from django_q.tasks import async_task
from django.utils import timezone

class ReprocessPoliciesCronJob(CronJobBase):
    RUN_EVERY_MINS = 3  # every 3 minutes

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'empPortal.reprocess_policies_cron'  # Unique code for the cron job

    def do(self):
        # Fetch all policies with status == 4
        policies_to_reprocess = PolicyDocument.objects.filter(status=4)

        for policy in policies_to_reprocess:
            try:
                # You can use a more complex logic to get the file_obj or task as needed
                file_status = policy.status
                if file_status == 5 or file_status == 3 or file_status == 4:
                    # Perform processing if the status matches the criteria
                    file_obj = FileAnalysis.objects.filter(policy_id=policy.id).last()
                    if file_obj:
                        async_task('empPortal.tasks.process_text_from_chatgpt', file_obj.id)

                if file_status == 1:
                    file_obj = ExtractedFile.objects.filter(policy_id=policy.id).last()
                    if file_obj:
                        async_task('empPortal.tasks.extract_pdf_text_task', file_obj.id)

            except PolicyDocument.DoesNotExist:
                print(f"File with ID {policy.id} not found in PolicyDocument")
            
            except FileAnalysis.DoesNotExist:
                print(f"File with ID {policy.id} not found in FileAnalysis")
                
            except ExtractedFile.DoesNotExist:
                print(f"File with ID {policy.id} not found in ExtractedFile")
        
        print(f"Reprocessed policies with status 4 at {timezone.now()}")
