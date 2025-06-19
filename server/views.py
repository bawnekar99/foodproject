from django.http import JsonResponse
from django.db import connection
from django.db.utils import OperationalError, DatabaseError
import logging
import traceback

# Set up logging
logger = logging.getLogger(__name__)

def server_status(request):
    """
    Check if the server is running and responsive.
    """
    try:
        return JsonResponse({
            "status": True,
            "message": "Server is running"
        }, status=200)
    except Exception as e:
        logger.error(f"Server status check failed: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({
            "status": False,
            "message": "Server check failed",
            "details": str(e) or "Unknown server error"
        }, status=500)

def db_status(request):
    from django.db import connection
    import traceback
    import logging

    logger = logging.getLogger(__name__)

    try:
        db_backend = connection.settings_dict['ENGINE']
        logger.info(f"Database backend: {db_backend}")

        connection.ensure_connection()

        # More reliable way: Use Django's introspection
        table_check = False
        try:
            table_list = connection.introspection.table_names()
            table_check = 'users_user' in table_list
        except Exception as table_error:
            logger.warning(f"Table check failed: {str(table_error)}")

        if table_check is True:
            status = True
            message = "Database connected successfully"
        else:
            status = False
            message = "Database connected but required table 'users_user' is missing"

        return JsonResponse({
            "status": status,
            "message": message,
            "details": f"Backend: {db_backend}, Table 'users_user' exists: {table_check}"
        }, status=200)

    except OperationalError as e:
        tb = traceback.format_exc()
        logger.error(f"Database connection failed: {str(e)}\n{tb}")
        return JsonResponse({
            "status": False,
            "message": "Database connection failed",
            "details": str(e) if str(e) else tb
        }, status=500)

    except DatabaseError as e:
        tb = traceback.format_exc()
        logger.error(f"Database operation failed: {str(e)}\n{tb}")
        return JsonResponse({
            "status": False,
            "message": "Database operation failed",
            "details": str(e) if str(e) else tb
        }, status=500)

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Unexpected error in db_status: {str(e)}\n{tb}")
        return JsonResponse({
            "status": False,
            "message": "Unexpected error occurred",
            "details": str(e) if str(e) else tb
        }, status=500)
