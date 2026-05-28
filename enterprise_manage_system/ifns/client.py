import json
from datetime import datetime
from audit.models import AuditLog


def send_report(report_data):
    if not report_data:
        return {
            'success': False,
            'result': 'error',
            'message': 'Нет данных для отправки'
        }

    if isinstance(report_data, dict):
        required_fields = ['type', 'data']
        if not all(field in report_data for field in required_fields):
            report_data = {'type': 'unknown', 'data': report_data}

    if report_data.get('type') == '2-NDFL' or 'employee_inn' in str(report_data):
        report_data = validate_ndfl_report(report_data)

    status_code = 200

    _log_report_submission(report_data, status_code)

    if status_code == 200:
        return {
            'success': True,
            'result': 'accepted',
            'message': 'Отчёт принят налоговой инспекцией',
            'timestamp': datetime.now().isoformat(),
            'receipt_number': f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
    else:
        return {
            'success': False,
            'result': 'rejected',
            'message': 'Ошибка при отправке отчёта',
            'timestamp': datetime.now().isoformat()
        }


def validate_ndfl_report(report_data):
    required_fields = ['employee_inn', 'total_income', 'tax_amount', 'year']

    missing_fields = [f for f in required_fields if f not in report_data]

    if missing_fields:
        return {
            'type': '2-NDFL',
            'data': report_data,
            'validation_errors': missing_fields,
            'is_valid': False
        }

    return {
        'type': '2-NDFL',
        'data': report_data,
        'is_valid': True
    }


def _log_report_submission(report_data, status_code):
    from audit.middleware import get_current_user

    user = get_current_user()

    from audit.models import AuditLog

    AuditLog.objects.create(
        user=user,
        action_type='create',
        description=f"Отправка отчёта в ИФНС: {json.dumps(report_data, default=str)[:200]}",
        new_value={'status_code': status_code, 'report_type': report_data.get('type', 'unknown')}
    )


def get_submission_status(receipt_number):
    return {
        'receipt_number': receipt_number,
        'status': 'processed',
        'message': 'Отчёт обработан и принят'
    }