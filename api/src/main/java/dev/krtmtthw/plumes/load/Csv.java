package dev.krtmtthw.plumes.load;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Minimal RFC 4180 reader (quoted fields, doubled quotes, CRLF) for the USGS and FIRMS CSV files. */
final class Csv {

    private Csv() { }

    static List<Map<String, String>> read(String text) {
        List<List<String>> records = parse(text);
        List<Map<String, String>> out = new ArrayList<>();
        if (records.isEmpty()) return out;
        List<String> header = records.get(0);
        for (List<String> rec : records.subList(1, records.size())) {
            if (rec.size() == 1 && rec.get(0).isEmpty()) continue;
            Map<String, String> row = new LinkedHashMap<>();
            for (int i = 0; i < header.size(); i++) row.put(header.get(i), i < rec.size() ? rec.get(i) : "");
            out.add(row);
        }
        return out;
    }

    static List<List<String>> parse(String text) {
        List<List<String>> records = new ArrayList<>();
        List<String> rec = new ArrayList<>();
        StringBuilder field = new StringBuilder();
        boolean quoted = false;
        for (int i = 0; i < text.length(); i++) {
            char ch = text.charAt(i);
            if (quoted) {
                if (ch == '"') {
                    if (i + 1 < text.length() && text.charAt(i + 1) == '"') { field.append('"'); i++; }
                    else quoted = false;
                } else field.append(ch);
            } else if (ch == '"') quoted = true;
            else if (ch == ',') { rec.add(field.toString()); field.setLength(0); }
            else if (ch == '\n' || ch == '\r') {
                if (ch == '\r' && i + 1 < text.length() && text.charAt(i + 1) == '\n') i++;
                rec.add(field.toString()); field.setLength(0);
                records.add(rec); rec = new ArrayList<>();
            } else field.append(ch);
        }
        if (field.length() > 0 || !rec.isEmpty()) { rec.add(field.toString()); records.add(rec); }
        return records;
    }
}
