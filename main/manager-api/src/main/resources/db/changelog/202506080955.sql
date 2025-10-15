-- Control panel enable wakeup word acceleration
UPDATE sys_params SET param_value = 'hello xiaozhi;hello xiaozhi;hey xiaoai;hello xiaoxin;hello xiaoxin;hey xiaomei;hey xiaolong;hey miaomiao;hey xiaobin;hey xiaobing;hey there' WHERE param_code = 'wakeup_words';
UPDATE sys_params SET param_value = 'true' WHERE param_code = 'enable_wakeup_words_response_cache';
