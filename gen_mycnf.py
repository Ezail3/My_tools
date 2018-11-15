#!/usr/bin/python
#-*- coding: UTF-8 -*-
#Author:Ezail

import argparse
import psutil

MYSQL_DATA_DIR = '/data/mysql/'
MYSQL_INSTALL_DIR = '/usr/local/'
MYSQL_CONF_DIR = '/etc/'
MYSQL_STARTUP_SCRIPT = '/etc/init.d/'


def _argparse():
    parser = argparse.ArgumentParser(description='MySQL Install Script...')
    parser.add_argument('--host', action='store', dest='host',
                        required=True, help='the server where u install the MySQL')
    parser.add_argument('-P', '--port', action='store', dest='port',
                        default=3306, type=int, help='the port number for connection 2 MySQL or 3306 4 default')
    parser.add_argument('-p', '--password', action='store', dest='password',
                        required=True, help='the password 4 root')
    parser.add_argument('-v', '--version', action='version', version='MySQL_Install 0.1')

    return parser.parse_args()

def get_innodb_buffer_pool_size(mem_sum):
    if mem_sum < 1024:
        innodb_buffer_pool_size = 128
    elif mem_sum < 4 * 1024:
        innodb_buffer_pool_size = mem_sum * 0.5
    else:
        innodb_buffer_pool_size = mem_sum * 0.75

    return int(innodb_buffer_pool_size)

def get_innodb_log_file_size(mem_sum):
    if mem_sum < 1024:
        innodb_log_file_size = 48
    elif mem_sum < 4 * 1024:
        innodb_log_file_size = 128
    elif mem_sum < 8 * 1024:
        innodb_log_file_size = 512
    elif mem_sum < 16 * 1024:
        innodb_log_file_size = 1024
    else:
        innodb_log_file_size = 2048

    return innodb_log_file_size

def get_innodb_max_undo_log_size(mem_sum):
    if mem_sum < 16 * 1024:
        innodb_max_undo_log_size = 1024
    else:
        innodb_max_undo_log_size = 2048

    return innodb_max_undo_log_size

def get_max_connections(mem_sum):
    max_connections = int(mem_sum * 0.3)
    max_connections = max_connections if max_connections < 1024 else 1024

    return max_connections

def get_session_mem_size(mem_free, max_connections):
    # read_rnd_buffer_size==sort_buffer_size==join_buffer_size==tmp_table_size==max_allowed_packet==read_buffer_size*2
    # max_connections/3 假设正常并发为最大连接数1/3，并且每个会话一次只使用一个buffer
	if mem_free / max_connections * 3 < 5:
		session_mem_size = 4
	elif mem_free / max_connections * 3 < 7:
		session_mem_size = 8
	elif mem_free / max_connections *3 < 19:
		session_mem_size = 16
	else:
		session_mem_size = 32
	
    session = dict(read_buffer_size=session_mem_size,
                   tmp_table_size=2 * session_mem_size,
                   join_buffer_size=2 * session_mem_size,
                   sort_buffer_size=2 * session_mem_size,
                   max_allowed_packet=2 * session_mem_size,
                   read_rnd_buffer_size=2 * session_mem_size)
    # session['read_buffer_size']
    return session

def get_thread_cache_size(mem_sum):
    mem_cache_size = 64 if mem_sum > 4 * 1024 else 32

    return mem_cache_size


var = _argparse()
core_num = psutil.cpu_count()
mem_sum = psutil.virtual_memory().total / 1000 / 1000
thread_set = core_num / 2 if core_num > 1 else 1

innodb_buffer_pool_size = str(get_innodb_buffer_pool_size(mem_sum)) + 'M'
innodb_log_file_size = str(get_innodb_log_file_size(mem_sum)) + 'M'
innodb_max_undo_log_size = str(get_innodb_max_undo_log_size(mem_sum)) + 'M'
thread_cache_size = str(get_thread_cache_size(mem_sum))
max_connections = get_max_connections(mem_sum)
max_user_connections = max_connections / 4
mem_free = mem_sum - get_innodb_buffer_pool_size(mem_sum) - get_innodb_log_file_size(
    mem_sum) - get_innodb_max_undo_log_size(mem_sum)

session = get_session_mem_size(mem_free, max_connections)

read_buffer_size = str(session['read_buffer_size']) + 'M'
read_rnd_buffer_size = str(session['read_rnd_buffer_size']) + 'M'
sort_buffer_size = str(session['sort_buffer_size']) + 'M'
tmp_table_size = str(session['tmp_table_size']) + 'M'
join_buffer_size = str(session['join_buffer_size']) + 'M'
max_allowed_packet = str(session['max_allowed_packet']) + 'M'

port = var.port
ip_addr = var.host
password = var.password
server_id = str(port) + ip_addr.split('.')[3]
datadir = MYSQL_DATA_DIR + 'mysql%s/data' % port
tmpdir = MYSQL_DATA_DIR + 'mysql%s/tmp' % port
pid_file = MYSQL_DATA_DIR + 'mysql%s/tmp/mysql.pid' % port
socket = MYSQL_DATA_DIR + 'mysql%s/tmp/mysql.sock' % port
log_bin = MYSQL_DATA_DIR + 'mysql%s/logs/binlog/mysql-bin' % port
relay_log = MYSQL_DATA_DIR + 'mysql%s/logs/relay.log' % port
slow_query_log_file = MYSQL_DATA_DIR + 'mysql%s/logs/slow.log' % port
log_error = MYSQL_DATA_DIR + 'mysql%s/logs/error.log' % port
general_log_file = MYSQL_DATA_DIR + 'mysql%s/logs/general.log' % port

innodb_buffer_pool_instances = thread_set
innodb_page_cleaners = thread_set
innodb_purge_threads = thread_set
slave_parallel_workers = thread_set
innodb_thread_concurrency = 4 * thread_set
table_open_cache_instances = 4 * thread_set
innodb_write_io_threads = thread_set
innodb_read_io_threads = thread_set


mycnf = '''
[client]
port	= %d
socket	= %s

[mysql]
prompt = (\\u@\\h) [\\d]>\\_

[mysqld]
# basic settings #
user = mysql
sql_mode = "STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER"
autocommit = 1
port = %d
server_id = %s
datadir= %s
tmpdir = %s
pid_file = %s
socket = %s
character_set_server = utf8mb4
transaction_isolation = READ-COMMITTED
explicit_defaults_for_timestamp = 1
max_allowed_packet = %s
event_scheduler = 1

# connection #
interactive_timeout = 1800
wait_timeout = 1800
lock_wait_timeout = 1800
skip_name_resolve = 1
max_connections = %d
max_user_connections = %d
max_connect_errors = 1000000
back_log = 1024

# table cache performance settings
table_open_cache = 4096
table_definition_cache = 4096
table_open_cache_instances = %d

# session memory settings #
read_buffer_size = %s
read_rnd_buffer_size = %s
sort_buffer_size = %s
tmp_table_size = %s
join_buffer_size = %s
thread_cache_size = %s
query_cache_type = 0
query_cache_size = 0

# log settings #
log_error = %s
log_bin = %s
log_error_verbosity = 2
general_log_file = %s
slow_query_log = 1
slow_query_log_file = %s
log_queries_not_using_indexes = 1
log_slow_admin_statements = 1
log_slow_slave_statements = 1
log_throttle_queries_not_using_indexes = 10
expire_logs_days = 90
long_query_time = 2
min_examined_row_limit = 100
log_bin_trust_function_creators = 1
log_slave_updates = 1

# replication settings #
master_info_repository = TABLE
relay_log_info_repository = TABLE
sync_binlog = 1
gtid_mode = 1
enforce_gtid_consistency = 1
log_slave_updates = 1
binlog_format = ROW
binlog_rows_query_log_events = 1
relay_log = %s
relay_log_recovery = 1
slave_skip_errors = ddl_exist_errors
slave_rows_search_algorithms = 'INDEX_SCAN,HASH_SCAN'

# semi sync replication settings #
plugin_dir = /usr/local/mysql/lib/plugin
plugin_load = "semisync_master.so;semisync_slave.so"
rpl_semi_sync_master_wait_point = after_sync
loose_rpl_semi_sync_master_enabled = 1
loose_rpl_semi_sync_slave_enabled = 1
loose_rpl_semi_sync_master_timeout = 3000

# innodb settings #
innodb_page_size = 16384
innodb_buffer_pool_size = %s
innodb_buffer_pool_instances = %d
innodb_buffer_pool_load_at_startup = 1
innodb_buffer_pool_dump_at_shutdown = 1
innodb_lru_scan_depth = 4096
innodb_lock_wait_timeout = 5
innodb_io_capacity = 10000
innodb_io_capacity_max = 20000
innodb_flush_method = O_DIRECT
innodb_open_files = 65535
innodb_undo_logs = 128
innodb_undo_tablespaces = 3
innodb_flush_neighbors = 0
innodb_log_file_size = %s
innodb_log_files_in_group = 2
innodb_log_buffer_size = 
innodb_purge_threads = %d
innodb_large_prefix = 1
innodb_thread_concurrency = %d
innodb_print_all_deadlocks = 1
innodb_strict_mode = 1
innodb_sort_buffer_size = 64M
innodb_write_io_threads = %d
innodb_read_io_threads = %d
innodb_file_per_table = 1
innodb_stats_persistent_sample_pages = 64
innodb_autoinc_lock_mode = 2
innodb_online_alter_log_max_size = 1G
innodb_open_files = 4096

[mysqld-5.7]
# new innodb settings #
loose_innodb_numa_interleave = 1
innodb_buffer_pool_dump_pct = 40
innodb_page_cleaners = %d
innodb_undo_log_truncate = 1
innodb_max_undo_log_size = %s
innodb_purge_rseg_truncate_frequency = 128

# new replication settings #
slave_parallel_type = LOGICAL_CLOCK
slave_parallel_workers = %d
slave_preserve_commit_order = 1
slave_transaction_retries = 128

# other change settings #
binlog_gtid_simple_recovery = 1
log_timestamps = 'system'
show_compatibility_56 = 1
''' % (port,
       socket,
       port,
       server_id,
       datadir,
       tmpdir,
       pid_file,
       socket,
       max_allowed_packet,
       max_connections,
       max_user_connections,
       table_open_cache_instances,
       read_buffer_size,
       read_rnd_buffer_size,
       sort_buffer_size,
       tmp_table_size,
       join_buffer_size,
       thread_cache_size,
       log_error,
       log_bin,
       general_log_file,
       slow_query_log_file,
       relay_log,
       innodb_buffer_pool_size,
       innodb_buffer_pool_instances,
       innodb_log_file_size,
       innodb_purge_threads,
       innodb_thread_concurrency,
       innodb_write_io_threads,
       innodb_read_io_threads,
       innodb_page_cleaners,
       innodb_max_undo_log_size,
       slave_parallel_workers
       )
