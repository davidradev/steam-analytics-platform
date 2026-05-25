{% macro pct_change(current_col, prev_col) %}
    case
        when {{ prev_col }} is null or {{ prev_col }} = 0 then null
        else round(({{ current_col }} - {{ prev_col }}) / {{ prev_col }}::float * 100, 2)
    end
{% endmacro %}
