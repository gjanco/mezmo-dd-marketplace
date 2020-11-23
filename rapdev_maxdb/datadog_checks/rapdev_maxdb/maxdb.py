# (C) RapDev, Inc. 2020-present
# All rights reserved
try:
    from datadog_checks.base import AgentCheck, ConfigurationError, is_affirmative
except ImportError:
    from checks import AgentCheck
from datadog_checks.base.utils.subprocess_output import get_subprocess_output

REQUIRED_TAGS = [
    "vendor:rapdev",
]

REQUIRED_SETTINGS = [
    "dbmcli",
    "hostname",
    "username",
    "password",
    "database"
]

class MaxDBCheck(AgentCheck):
    def __init__(self, *args, **kwargs):
        super(MaxDBCheck, self).__init__(*args, **kwargs)
        self.dbmcli   = self.instance.get("dbmcli")
        self.hostname = self.instance.get("hostname")
        self.database = self.instance.get("database")

        self.username      = self.instance.get("username")
        self.password      = self.instance.get("password")
        self.userpass      = self.username + "," + self.password
        
        self.enable_uptime = is_affirmative(self.instance.get("uptime_enabled", False))
        self.metric_prefix = "rapdev.maxdb"
        self.tags = REQUIRED_TAGS + self.instance.get("tags", [])
        self.tags.append("db:{}".format(self.database))
        self.tags.append("maxdb_host:{}".format(self.hostname))
        self.billing_metric = "{}.{}".format("datadog.marketplace", self.metric_prefix)

    def check(self, instance):
        self.validate_config()
        self.check_db_connect()

        self.gauge(self.billing_metric, 1.0, tags=self.tags)
        statecheck = self.check_db_state()

        if statecheck == 1:
            self.query_backup_threads()
            self.query_cache_stats()
            self.query_catalog_cache()
            self.query_command_cache()
            self.query_command_stats()
            self.query_data_cache()
            self.query_data_stats()
            self.query_data_volumes()
            self.query_lock_stats()
            self.query_log_stats()
            self.query_log_volumes()
            self.query_oms_heap_stats()
            self.query_schema_size()
            self.query_sessions()
            self.query_table_size()

        if self.enable_uptime == True:
            self.check_db_uptime()
            
    def validate_config(self):
        if not self.dbmcli:
            raise ConfigurationError("Path to dbmcli is needed")
        if not self.hostname or not self.database:
            raise ConfigurationError("MaxDB hostname and database are needed")
        if not self.username or not self.password:
            raise ConfigurationError("MaxDB username and password are needed")

    def check_db_state(self):
        output = get_subprocess_output([self.dbmcli, "-u", self.userpass , "-d", self.database, "-n", self.hostname, "db_state"],self.log, raise_on_empty_output=True)
        cli_out = str(output[0]).splitlines()
        x = 2
        data = cli_out[x:]
        if data[0] == "ONLINE":
            state = 1
        elif data[0] == "ADMIN":
            state = 2
        elif data[0] == "OFFLINE":
            state = 3
        elif data[0] == "STANDBY":
            state = 4
        elif data[0] == "STOPPED INCORRECTLY":
            state = 5
        elif data[0] == "UNKNOWN":
            state = 6
        else:
            self.log.debug("Could not identify database state, got: %s", data[0])
            state = 0
        self.gauge("{}.db_state".format(self.metric_prefix), state, tags=self.tags)
        return state

    def check_db_connect(self):
        output = get_subprocess_output([self.dbmcli, "-u", self.userpass , "-d", self.database, "-n", self.hostname, "db_connect"],self.log, raise_on_empty_output=True)
        cli_out = str(output[0]).splitlines()
        if cli_out[0] == "OK":
            self.service_check("{}.can_connect".format(self.metric_prefix), AgentCheck.OK, tags=self.tags)
        else:
            self.service_check("{}.can_connect".format(self.metric_prefix), AgentCheck.CRITICAL, tags=self.tags)

    def check_db_uptime(self):
        output = get_subprocess_output([self.dbmcli, "-u", self.userpass , "-d", self.database, "-n", self.hostname, "show", "UPTIME"],self.log, raise_on_empty_output=True)
        cli_out = str(output[0]).splitlines()
        uptimestr = str(cli_out[4])
        uptimelist = uptimestr.split()
        
        days = int(uptimelist[2])
        hours = int(uptimelist[4])
        minutes = int(uptimelist[6])
        seconds = int(uptimelist[8])

        db_uptime = (days * 86400) + (hours * 3600) + (minutes * 60) + seconds

        self.gauge("{}.uptime".format(self.metric_prefix), db_uptime, tags=self.tags)

    def run_query(self, query):
        output = get_subprocess_output([self.dbmcli, "-u", self.userpass , "-d", self.database, "-n", self.hostname, "db_execute", query],self.log, raise_on_empty_output=True)
        cli_out = str(output[0]).splitlines()
        
        if cli_out[0] == "ERR":
            data = 0
        else:
            x = 2
            datalist = cli_out[x:]
            
            data = []
            for item in datalist:
                itemlist = item.split(";")
                data.append(itemlist)

        return data

    def query_backup_threads(self):
        bkp_threads = self.run_query("SELECT THREADNAME, IOCOUNT, IOPAGECOUNT, IOTIME, PENDINGIOCOUNT, PATH FROM SYSINFO.BACKUPTHREADS")
        if bkp_threads is not 0:
            metric_tags = self.tags.copy()
            metric_tags.append("thread:{}".format(self.parse_string(bkp_threads[0][0])))
            metric_tags.append("backup_medium:{}".format(self.parse_string(bkp_threads[0][5])))
            bkp_io_count = float(bkp_threads[0][1])
            bkp_io_page_count = float(bkp_threads[0][2])
            bkp_io_time = float(bkp_threads[0][3])
            bkp_pending_io_count = float(bkp_threads[0][4])
            self.gauge("{}.backup.io_operations".format(self.metric_prefix), bkp_io_count, tags=metric_tags)
            self.gauge("{}.backup.io_pages".format(self.metric_prefix), bkp_io_page_count, tags=metric_tags)
            self.gauge("{}.backup.io_time".format(self.metric_prefix), bkp_io_time, tags=metric_tags)
            self.gauge("{}.backup.pending_io_operations".format(self.metric_prefix), bkp_pending_io_count, tags=metric_tags)

    def query_cache_stats(self):
        cache_stats = self.run_query("SELECT NAME, ACCESSCOUNT, SUCCESSFULACCESSCOUNT, UNSUCCESSFULACCESSCOUNT, HITRATE FROM SYSINFO.CACHESTATISTICS")
        for item in cache_stats:
            metric_tags = self.tags.copy()
            metric_tags.append("cache:{}".format(self.parse_string(item[0])))
            cache_accesses = float(item[1])
            cache_hits = float(item[2])
            cache_misses = float(item[3])
            if self.parse_string(item[4]) == "(null)":
                cache_hitrate = 0
            else:
                cache_hitrate = float(item[4])
            if cache_misses == 0:
                cache_missrate = 0
            else:
                cache_missrate = float(cache_misses/cache_accesses)
            self.gauge("{}.cache.accesses".format(self.metric_prefix), cache_accesses, tags=metric_tags)
            self.gauge("{}.cache.hits".format(self.metric_prefix), cache_hits, tags=metric_tags)
            self.gauge("{}.cache.misses".format(self.metric_prefix), cache_misses, tags=metric_tags)
            self.gauge("{}.cache.hit_rate".format(self.metric_prefix), cache_hitrate, tags=metric_tags)
            self.gauge("{}.cache.miss_rate".format(self.metric_prefix), cache_missrate, tags=metric_tags)
    
    def query_catalog_cache(self):
        catalog_cache_stats = self.run_query("SELECT ENTRYCOUNT, LRUENTRYCOUNT, INVALIDHANDLECOUNT FROM SYSINFO.CATALOGCACHESTATISTICS")
        catcache_entrycount = float(catalog_cache_stats[0][0])
        catcache_lru_entrycount = float(catalog_cache_stats[0][1])
        catcache_invalid_count = float(catalog_cache_stats[0][2])
        self.gauge("{}.catalog_cache.entrycount".format(self.metric_prefix), catcache_entrycount, tags=self.tags)
        self.gauge("{}.catalog_cache.lru_entrycount".format(self.metric_prefix), catcache_lru_entrycount, tags=self.tags)
        self.gauge("{}.catalog_cache.invalid_entrycount".format(self.metric_prefix), catcache_invalid_count, tags=self.tags)

    def query_command_cache(self):
        cmd_cache_stats = self.run_query("SELECT USABLESIZE, USEDSIZE, USEDSIZEPERCENTAGE, COMMANDCOUNT, INSERTCOMMANDCOUNT, DELETECOMMANDCOUNT, CLEANUPCOUNT FROM SYSINFO.COMMANDCACHESTATISTICS")
        cmdcache_usable_size = float(cmd_cache_stats[0][0])
        cmdcache_used_size = float(cmd_cache_stats[0][1])
        cmdcache_in_use = float(cmd_cache_stats[0][2])
        cmdcache_cmd_count = float(cmd_cache_stats[0][3])
        cmdcache_insert = float(cmd_cache_stats[0][4])
        cmdcache_delete = float(cmd_cache_stats[0][5])
        cmdcache_cleanup = float(cmd_cache_stats[0][6])
        self.gauge("{}.command_cache.usable_size".format(self.metric_prefix), cmdcache_usable_size, tags=self.tags)
        self.gauge("{}.command_cache.used_size".format(self.metric_prefix), cmdcache_used_size, tags=self.tags)
        self.gauge("{}.command_cache.in_use".format(self.metric_prefix), cmdcache_in_use, tags=self.tags)
        self.gauge("{}.command_cache.command_count".format(self.metric_prefix), cmdcache_cmd_count, tags=self.tags)
        self.gauge("{}.command_cache.insert_command".format(self.metric_prefix), cmdcache_insert, tags=self.tags)
        self.gauge("{}.command_cache.delete_command".format(self.metric_prefix), cmdcache_delete, tags=self.tags)
        self.gauge("{}.command_cache.cleanup".format(self.metric_prefix), cmdcache_cleanup, tags=self.tags)

    def query_command_stats(self):
        command_stats = self.run_query("SELECT COMMANDID, USERNAME, SCHEMANAME, EXECUTECOUNT, RUNTIME, READROWCOUNT, PHYSICALREADCOUNT, VIRTUALREADCOUNT, READPAGECOUNT, WRITEPAGECOUNT, IOREADCOUNT, IOWRITECOUNT, STATEMENT FROM SYSINFO.COMMANDSTATISTICS")
        if command_stats is not 0:
            for item in command_stats:
                metric_tags = self.tags.copy()
                metric_tags.append("command_id:{}".format(self.parse_string(item[0])))
                metric_tags.append("username:{}".format(self.parse_string(item[1])))
                metric_tags.append("schema:{}".format(self.parse_string(item[2])))
                metric_tags.append("sql_statement:{}".format(self.parse_string(item[12])))
                execute_count = float(command_stats[3])
                runtime = float(command_stats[4])
                read_row_count = float(command_stats[5])
                physical_read_count = float(command_stats[6])
                virtual_read_count = float(command_stats[7])
                read_page_count = float(command_stats[8])
                write_page_count = float(command_stats[9])
                io_read_count = float(command_stats[10])
                io_write_count = float(command_stats[11])
                total_io = (io_read_count+io_write_count)
                self.gauge("{}.command.execute_count".format(self.metric_prefix), execute_count, tags=metric_tags)
                self.gauge("{}.command.runtime".format(self.metric_prefix), runtime, tags=metric_tags)
                self.gauge("{}.command.rows_read".format(self.metric_prefix), read_row_count, tags=metric_tags)
                self.gauge("{}.command.physical_reads".format(self.metric_prefix), physical_read_count, tags=metric_tags)
                self.gauge("{}.command.virtual_reads".format(self.metric_prefix), virtual_read_count, tags=metric_tags)
                self.gauge("{}.command.pages_read".format(self.metric_prefix), read_page_count, tags=metric_tags)
                self.gauge("{}.command.pages_written".format(self.metric_prefix), write_page_count, tags=metric_tags)
                self.gauge("{}.command.io_reads".format(self.metric_prefix), io_read_count, tags=metric_tags)
                self.gauge("{}.command.io_writes".format(self.metric_prefix), io_write_count, tags=metric_tags)
                self.gauge("{}.command.total_io".format(self.metric_prefix), total_io, tags=metric_tags)

    def query_data_cache(self):
        data_cache_stats = self.run_query("SELECT USABLESIZE, USEDSIZE, OMSDATASIZE, HISTORYDATASIZE, SQLDATASIZE, USEDPINAREASIZE, USABLEPINAREASIZE FROM SYSINFO.DATACACHE")
        datacache_usable_size = float(data_cache_stats[0][0])
        datacache_used_size = float(data_cache_stats[0][1])
        datacache_oms_size = float(data_cache_stats[0][2])
        datacache_history_size = float(data_cache_stats[0][3])
        datacache_sql_size = float(data_cache_stats[0][4])
        datacache_pinarea_used_size = float(data_cache_stats[0][5])
        datacache_pinarea_usable_size = float(data_cache_stats[0][6])
        datacache_in_use = (datacache_used_size / datacache_usable_size)
        datacache_pinarea_in_use = (datacache_pinarea_used_size / datacache_pinarea_usable_size)
        self.gauge("{}.data_cache.usable_size".format(self.metric_prefix), datacache_usable_size, tags=self.tags)
        self.gauge("{}.data_cache.used_size".format(self.metric_prefix), datacache_used_size, tags=self.tags)
        self.gauge("{}.data_cache.oms_size".format(self.metric_prefix), datacache_oms_size, tags=self.tags)
        self.gauge("{}.data_cache.history_size".format(self.metric_prefix), datacache_history_size, tags=self.tags)
        self.gauge("{}.data_cache.sql_size".format(self.metric_prefix), datacache_sql_size, tags=self.tags)
        self.gauge("{}.data_cache.pinarea_used_size".format(self.metric_prefix), datacache_pinarea_used_size, tags=self.tags)
        self.gauge("{}.data_cache.pinarea_usable_size".format(self.metric_prefix), datacache_pinarea_usable_size, tags=self.tags)
        self.gauge("{}.data_cache.in_use".format(self.metric_prefix), datacache_in_use, tags=self.tags)
        self.gauge("{}.data_cache.pinarea_in_use".format(self.metric_prefix), datacache_pinarea_in_use, tags=self.tags)

    def query_data_stats(self):
        data_stats = self.run_query("SELECT USABLESIZE, USEDSIZE, USEDSIZEPERCENTAGE, USEDPERMANENTSIZE, USEDTEMPORARYSIZE, USEDPERMANENTCONVERTERSIZE, USEDTEMPORARYCONVERTERSIZE, INCREMENTALBACKUPSIZE, USEDSHADOWSIZE FROM SYSINFO.DATASTATISTICS")
        data_usable_size = float(data_stats[0][0])
        data_used_size = float(data_stats[0][1])
        data_in_use = float(data_stats[0][2])
        perm_data_used = float(data_stats[0][3])
        temp_data_used = float(data_stats[0][4])
        perm_converter_used_size = float(data_stats[0][5])
        temp_converter_used_size = float(data_stats[0][6])
        incremental_bkp_size = float(data_stats[0][7])
        shadow_used_size = float(data_stats[0][8])
        data_free_size = (data_usable_size - data_used_size)
        data_free_pct = (100 - data_in_use)
        self.gauge("{}.data.usable_size".format(self.metric_prefix), data_usable_size, tags=self.tags)
        self.gauge("{}.data.used_size".format(self.metric_prefix), data_used_size, tags=self.tags)
        self.gauge("{}.data.in_use".format(self.metric_prefix), data_in_use, tags=self.tags)
        self.gauge("{}.data.free_size".format(self.metric_prefix), data_free_size, tags=self.tags)
        self.gauge("{}.data.free".format(self.metric_prefix), data_free_pct, tags=self.tags)
        self.gauge("{}.data.permanent_data_used".format(self.metric_prefix), perm_data_used, tags=self.tags)
        self.gauge("{}.data.temporary_data_used".format(self.metric_prefix), temp_data_used, tags=self.tags)
        self.gauge("{}.data.permanent_converter_data_used".format(self.metric_prefix), perm_converter_used_size, tags=self.tags)        
        self.gauge("{}.data.temporary_converter_data_used".format(self.metric_prefix), temp_converter_used_size, tags=self.tags)
        self.gauge("{}.data.pending_incremental_backup_size".format(self.metric_prefix), incremental_bkp_size, tags=self.tags)
        self.gauge("{}.data.shadow_used_size".format(self.metric_prefix), shadow_used_size, tags=self.tags)

    def query_data_volumes(self):
        data_vols_stats = self.run_query("SELECT MODE, USABLESIZE, USEDSIZE, USEDSIZEPERCENTAGE, PATH FROM SYSINFO.DATAVOLUMES")
        for item in data_vols_stats:
            metric_tags = self.tags.copy()
            metric_tags.append("mode:{}".format(self.parse_string(item[0])))
            metric_tags.append("volume:{}".format(self.parse_string(item[4])))
            datavol_usable_size = float(item[1])
            datavol_used_size = float(item[2])
            datavol_in_use = float(item[3])
            self.gauge("{}.data_volume.usable_size".format(self.metric_prefix), datavol_usable_size, tags=metric_tags)
            self.gauge("{}.data_volume.used_size".format(self.metric_prefix), datavol_used_size, tags=metric_tags)
            self.gauge("{}.data_volume.in_use".format(self.metric_prefix), datavol_in_use, tags=metric_tags)
    
    def query_lock_stats(self):
        lock_stats = self.run_query("SELECT ENTRYCOUNT, USEDENTRYCOUNT, USEDENTRYCOUNTPERCENTAGE, TABLELOCKCOUNT, ROWLOCKCOUNT, LOCKESCALATIONCOUNT, SQLLOCKCOLLISIONCOUNT, OMSLOCKCOLLISIONCOUNT, DEADLOCKCOUNT, SQLREQUESTTIMEOUTCOUNT, OMSREQUESTTIMEOUTCOUNT FROM SYSINFO.LOCKSTATISTICS")
        lock_entries = float(lock_stats[0][0])
        lock_entries_used = float(lock_stats[0][1])
        lock_utilization = float(lock_stats[0][2])
        table_lock_count = float(lock_stats[0][3])
        row_lock_count = float(lock_stats[0][4])
        lock_escalation_count = float(lock_stats[0][5])
        sql_collision_count = float(lock_stats[0][6])
        oms_collision_count = float(lock_stats[0][7])
        deadlock_count = float(lock_stats[0][8])
        sql_timeout_count = float(lock_stats[0][9])
        oms_timeout_count = float(lock_stats[0][10])
        self.gauge("{}.locks.available".format(self.metric_prefix), lock_entries, tags=self.tags)
        self.gauge("{}.locks.used".format(self.metric_prefix), lock_entries_used, tags=self.tags)
        self.gauge("{}.locks.utilization".format(self.metric_prefix), lock_utilization, tags=self.tags)
        self.gauge("{}.locks.table_locks".format(self.metric_prefix), table_lock_count, tags=self.tags)
        self.gauge("{}.locks.row_locks".format(self.metric_prefix), row_lock_count, tags=self.tags)
        self.gauge("{}.locks.lock_escalations".format(self.metric_prefix), lock_escalation_count, tags=self.tags)
        self.gauge("{}.locks.sql_collisions".format(self.metric_prefix), sql_collision_count, tags=self.tags)
        self.gauge("{}.locks.oms_collisions".format(self.metric_prefix), oms_collision_count, tags=self.tags)
        self.gauge("{}.locks.deadlocks".format(self.metric_prefix), deadlock_count, tags=self.tags)
        self.gauge("{}.locks.sql_timeouts".format(self.metric_prefix), sql_timeout_count, tags=self.tags)
        self.gauge("{}.locks.oms_timeouts".format(self.metric_prefix), oms_timeout_count, tags=self.tags)

    def query_log_stats(self):
        log_stats = self.run_query("SELECT USABLESIZE, USEDSIZE, USEDSIZEPERCENTAGE, NOTSAVEDSIZE, NOTSAVEDPERCENTAGE, QUEUESIZE FROM SYSINFO.LOGSTATISTICS")
        log_usable_size = float(log_stats[0][0])
        log_used_size = float(log_stats[0][1])
        log_in_use = float(log_stats[0][2])
        log_not_saved_size = float(log_stats[0][3])
        log_not_saved = float(log_stats[0][4])
        log_queue_size = float(log_stats[0][5])
        self.gauge("{}.log.usable_size".format(self.metric_prefix), log_usable_size, tags=self.tags)
        self.gauge("{}.log.used_size".format(self.metric_prefix), log_used_size, tags=self.tags)
        self.gauge("{}.log.in_use".format(self.metric_prefix), log_in_use, tags=self.tags)
        self.gauge("{}.log.not_saved_size".format(self.metric_prefix), log_not_saved_size, tags=self.tags)
        self.gauge("{}.log.not_saved".format(self.metric_prefix), log_not_saved, tags=self.tags)
        self.gauge("{}.log.queue_size".format(self.metric_prefix), log_queue_size, tags=self.tags)

    def query_log_volumes(self):
        log_vols_stats = self.run_query("SELECT ID, CONFIGUREDSIZE, USABLESIZE, PATH FROM SYSINFO.LOGVOLUMES")
        for item in log_vols_stats:
            metric_tags = self.tags.copy()
            metric_tags.append("id:{}".format(self.parse_string(item[0])))
            metric_tags.append("volume:{}".format(self.parse_string(item[3])))
            logvol_conf_size = float(item[1])
            logvol_usable_size = float(item[2])
            self.gauge("{}.log_volume.configured_size".format(self.metric_prefix), logvol_conf_size, tags=metric_tags)
            self.gauge("{}.log_volume.usable_size".format(self.metric_prefix), logvol_usable_size, tags=metric_tags)

    def query_oms_heap_stats(self):
        oms_heap_stats = self.run_query("SELECT DESCRIPTION, TOTAL_HEAP_USAGE, RESERVED FROM OMS_HEAP_STATISTICS")
        for item in oms_heap_stats:
            metric_tags = self.tags.copy()
            metric_tags.append("allocator:{}".format(self.parse_string(item[0])))
            heap_used_size = float(item[1])/1024
            heap_reserved = float(item[2])/1024
            if heap_used_size == 0:
                heap_utilization = 0
            else:
                heap_utilization = (heap_used_size/heap_reserved)*100
            self.gauge("{}.oms_heap.used_size".format(self.metric_prefix), heap_used_size, tags=metric_tags)
            self.gauge("{}.oms_heap.reserved_size".format(self.metric_prefix), heap_reserved, tags=metric_tags)
            self.gauge("{}.oms_heap.utilization".format(self.metric_prefix), heap_utilization, tags=metric_tags)

    def query_schema_size(self):
        schema_size_stats = self.run_query("SELECT SCHEMANAME, USEDSIZE FROM SYSINFO.SCHEMASIZE")
        for item in schema_size_stats:
            metric_tags = self.tags.copy()
            metric_tags.append("schema:{}".format(self.parse_string(item[0])))
            schema_used_size = float(item[1])
            self.gauge("{}.schema.used_size".format(self.metric_prefix), schema_used_size, tags=metric_tags)

    def query_sessions(self):
        session_stats = self.run_query("SELECT SESSIONID, STARTDATE, APPLICATIONNODE, APPLICATIONTYPE, USERNAME, OMSHEAPUSEDSIZE, CATALOGCACHEUSEDSIZE, USEDTEMPORARYSIZE, PAGINGFILEUSEDSIZE, CURRENTSCHEMANAME FROM SYSINFO.SESSIONS")
        max_tasks_result = self.run_query("SELECT VALUE FROM SYSINFO.ACTIVECONFIGURATION WHERE PARAMETERNAME = 'MAXUSERTASKS'")
        session_count = len(session_stats)
        max_user_tasks = float(self.parse_string(max_tasks_result[0][0]))
        session_utilization = (session_count/max_user_tasks)*100
        self.gauge("{}.session.count".format(self.metric_prefix), session_count, tags=self.tags)
        self.gauge("{}.session.utilization".format(self.metric_prefix), session_utilization, tags=self.tags)
        for item in session_stats:
            metric_tags = self.tags.copy()
            metric_tags.append("session_id:{}".format(self.parse_string(item[0])))
            metric_tags.append("applicationnode:{}".format(self.parse_string(item[2])))
            metric_tags.append("applicationtype:{}".format(self.parse_string(item[3])))
            metric_tags.append("applicationuser:{}".format(self.parse_string(item[4])))
            metric_tags.append("schema:{}".format(self.parse_string(item[9])))
            if self.parse_string(item[5]) == "(null)":
                omsheap_used_size = 0
            else:
                omsheap_used_size = float(item[5])
            catcache_used_size = float(item[6])
            temp_used_size = float(item[7])
            pagingfile_used_size = float(item[8])
            self.gauge("{}.session.oms_heap_used_size".format(self.metric_prefix), omsheap_used_size, tags=metric_tags)
            self.gauge("{}.session.catalog_cache_used_size".format(self.metric_prefix), catcache_used_size, tags=metric_tags)
            self.gauge("{}.session.temp_used_size".format(self.metric_prefix), temp_used_size, tags=metric_tags)
            self.gauge("{}.session.paging_file_used_size".format(self.metric_prefix), pagingfile_used_size, tags=metric_tags)

    def query_table_size(self):
        table_size_stats = self.run_query("SELECT SCHEMANAME, TABLENAME, USEDSIZE, ROWCOUNT FROM SYSINFO.TABLESIZE")
        for item in table_size_stats:
            metric_tags = self.tags.copy()
            metric_tags.append("schema:{}".format(self.parse_string(item[0])))
            metric_tags.append("table:{}".format(self.parse_string(item[1])))
            table_used_size = float(item[2])
            table_row_count = float(item[3])
            self.gauge("{}.table.used_size".format(self.metric_prefix), table_used_size, tags=metric_tags)
            self.gauge("{}.table.row_count".format(self.metric_prefix), table_row_count, tags=metric_tags)
    
    def parse_string(self, string):
        newstring = string.replace("'", "")
        return newstring
