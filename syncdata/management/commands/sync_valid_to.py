import logging
from django.core.management.base import BaseCommand, CommandError
from syncdata.tasks import sync_valid_to

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Sync valid data to database"
    def handle(self, *args, **options):
        logger.info("Starting VALID_TO sync...")
        sync_valid_to()
        logger.info("Finished VALID_TO sync")