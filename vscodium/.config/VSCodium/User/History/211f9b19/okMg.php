<?php
/**
 * @file CoreLogController.php
 * @path app/Http/Controllers/Api/Core/CoreLogController.php
 * @project JS web-platform
 * @author JS
 * @created 2026
 * @description Read/write access to the system-wide audit log (core_logs) - authentication
 * events, user/role/permission management, legal document changes, core site settings. The
 * endpoints are shared by AuditLogController; this class only names the model and the resource.
 * @dependencies
 * - App\Http\Controllers\Api\AuditLogController: index / store / show.
 */

namespace App\Http\Controllers\Api\Core;

use App\Http\Controllers\Api\AuditLogController;
use App\Http\Resources\Core\CoreLogResource;
use App\Models\Core\CoreLog;

class CoreLogController extends AuditLogController
{
    /** @description Model of core_logs. */
    protected function model(): string
    {
        return CoreLog::class;
    }

    /** @description Resource of one core_logs row. */
    protected function resource(): string
    {
        return CoreLogResource::class;
    }
}