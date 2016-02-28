package us.kbase.genbank;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.PrintWriter;
import java.util.List;
import java.util.StringTokenizer;

/**
 * Parser of GBK-files.
 */
public class GbkParser {
    public static final int HEADER_PREFIX_LENGTH = 12;
    public static final int FEATURE_PREFIX_LENGTH = 21;

    /**
     * @param br
     * @param params
     * @param filename
     * @param ret
     * @throws Exception
     */
    public static void parse(BufferedReader br, GbkParsingParams params, String filename, GbkCallback ret) throws Exception {
        TypeManager qual_tm = new TypeManager("qualifier_types.properties");
        String SUBHEADER_ORGANISM_TYPE = "ORGANISM";
        String QUALIFIER_DB_XREF_TYPE = "db_xref";
        String QUALIFIER_NOTE_TYPE = "note";
        String QUALIFIER_TRANSLATION_TYPE = "translation";
        int state = 0;
        GbkLocus loc = null;
        GbkSequence seq = null;
        GbkHeader head = null;
        GbkSubheader sub = null;
        GbkFeature feat = null;
        GbkQualifier qual = null;
        int line_num = 1;
        try {
            for (; ; line_num++) {
                String line = br.readLine();
                if (line == null) break;
                if (line.trim().length() == 0) continue;
                if (state == -1) {   // Skipping current locus
                    if (line.startsWith("//")) state = 0;
                    continue;
                } else if (state == 0) {
                    if (line.startsWith("FEATURES")) {
                        if (loc != null) {
                            if (!loc.isClosed()) loc.closeHeaders(filename);
                        }
                        state = 1;
                        continue;
                    }
                    String prefix = line.substring(0, HEADER_PREFIX_LENGTH);
                    line = line.substring(HEADER_PREFIX_LENGTH).trim();
                    if (prefix.trim().length() > 0) {
                        if (prefix.startsWith("LOCUS")) {
                            StringTokenizer st = new StringTokenizer(line, " \t");
                            if ((loc != null) && (!loc.isClosed())) loc.close(filename);
                            loc = new GbkLocus(line_num, st.nextToken(), ret);
                            head = null;
                            sub = null;
                        }
                        if (prefix.startsWith(" ")) {
                            sub = new GbkSubheader(line_num, prefix.trim(), line);
                            head.subheaders.add(sub);
                        } else {
                            String type = prefix.trim();
                            head = new GbkHeader(line_num, type, line);
                            sub = null;
                            loc.addHeader(head, filename);
                        }
                    } else {
                        if (sub != null) {
                            if (sub.type.equals(SUBHEADER_ORGANISM_TYPE)) {
                                sub.appendValueWithoutSpace("\n" + line);
                            } else {
                                sub.appendValue(line);
                            }
                        } else {
                            head.appendValue(line);
                        }
                    }
                } else if (state == 1) {
                    if (line.startsWith("ORIGIN") || line.startsWith("CONTIG ")) {
                        state = 2;
                        if (qual != null) qual.close();
                        qual = null;
                        if (feat != null) feat.close(params);
                        feat = null;
                        if (!loc.isClosed()) {
                            loc.close(filename);
                        }
                        seq = new GbkSequence(loc, ret);
                        loc = null;
                        continue;
                    }
                    if (line.startsWith("BASE COUNT")) continue;
                    String prefix = line.substring(0, FEATURE_PREFIX_LENGTH).trim();
                    line = line.substring(FEATURE_PREFIX_LENGTH).trim();

                    //System.out.println("qual "+qual+"\tfeat "+feat);
                    if (prefix.length() > 0) {
                        if (feat != null) {
                            feat.close(params);
                        }
                        feat = new GbkFeature(line_num, prefix, line);

                        if (qual != null) {
                            //System.out.println("qual.close() " + qual.value);
                            qual.close();
                        }
                        qual = null;

                        loc.addFeature(feat, filename);
                    } else if (line.indexOf("/") == 0 && line.indexOf("/ ") != 0 && line.indexOf("=") == -1 && line.indexOf("\"") == -1) {//skips illegal features with no '=' and no quotes

                        //System.err.println("qual " + qual);
                        System.out.println("Warning parsing GBK file: ignoring field [" + line + "], non-standard qualifier not confirming to /X=\"Y\"");
                        continue;

                        /*if (line.equals("/pseudo") || line.equals("/trans_splicing") || line.equals("/ribosomal_slippage")) {

                            if (qual != null) {
                                String s = qual.toString();
                                //System.out.println("qual " + s);
                                if (s.endsWith("\")"))
                                    s = s.substring(0, s.length() - 2);

                                //if (s.substring(s.length() - 1, s.length()).equals("\""))
                                //if (qual.type.equals(QUALIFIER_DB_XREF_TYPE) || qual.type.equals(QUALIFIER_TRANSLATION_TYPE)) {
                                //    qual.value = new StringBuffer(s + ";" + line.substring(1) + "\");");
                                //    //System.out.println("qual 1 " + qual.value);
                                //}
                                if(qual.type.equals(QUALIFIER_NOTE_TYPE)) {
                                    qual.value = new StringBuffer(s + ";" + " " + line.substring(1) + "\");");
                                    //System.out.println("qual 2 " + qual.value);
                                }
                            }
                            else {
                            //feat.appendValue(line);

                            System.out.println("special " + line);
                            String s = feat.toString();
                            if (s.endsWith(";)\""))
                                s = s.substring(0, s.length() - 3);
                            feat.value = new StringBuffer(s + ";" + " " + line.substring(1) + "\");");
                            System.out.println("feat " + feat.value);
                            }
                        }*/

                        //continue;
                    } else {

                        if (qual == null && (line.startsWith("/")) &&//added qual = null to allow feature text which spans multiple lines and potentially starts with a '/'
                                (!line.startsWith("/ ")) && // these are continued strings with slashes from previous line
                                (line.indexOf("=") == -1)) {
                            if (!qual_tm.isType(line.substring(1)))
                                System.out.println("Warning parsing GBK file: ignoring field B [" + line.substring(1) + "]");
                            line += "=";
                        }
                        int slash_pos = line.indexOf("/");
                        int equal_pos = line.indexOf("=");
                        String qual_name = null;
                        if ((slash_pos == 0) && (1 < equal_pos)) {
                            qual_name = line.substring(slash_pos + 1, equal_pos).trim();
                            if (qual_name.length() == 0) {
                                qual_name = null;
                            } else {
                                for (int i = 0; i < qual_name.length(); i++) {
                                    char ch = qual_name.charAt(i);
                                    if ((!Character.isLetterOrDigit(ch)) &&
                                            (ch != '_')) {
                                        qual_name = null;
                                        break;
                                    }
                                }
                            }
                        }
                        if (qual_name != null) {
                            line = line.substring(equal_pos + 1).trim();
                            if (qual != null) qual.close();
                            qual = new GbkQualifier(line_num, qual_name, line);

                            feat.qualifiers.add(qual);
                        } else {
                            if (qual != null) {
                                if (qual.type.equals(QUALIFIER_DB_XREF_TYPE) || qual.type.equals(QUALIFIER_TRANSLATION_TYPE)) {
                                    qual.appendValueWithoutSpace(line);
                                } else {
                                    qual.appendValue(line);
                                    /*if (line.equals("/pseudo") || line.equals("/trans_splicing") || line.equals("/ribosomal_slippage")) {
                                        System.out.println("specialappend qual");
                                    }*/
                                }
                            } else {
                                feat.appendValue(line);
                                /*if (line.equals("/pseudo") || line.equals("/trans_splicing") || line.equals("/ribosomal_slippage")) {
                                    System.out.println("specialappend feat");
                                }*/
                            }
                        }
                    }
                } else if (state == 2) {
                    if (line.startsWith("//")) {
                        seq.close(filename);
                        seq = null;
                        state = 0;
                        continue;
                    }
                    StringTokenizer st = new StringTokenizer(line, " \t");
                    st.nextToken();
                    while (st.hasMoreTokens()) {
                        seq.append(st.nextToken(), filename);
                    }
                }
            }
        } catch (Throwable t) {
            System.out.println("Error parsing GBK file " + filename + " at line " + line_num);
            throw new IllegalStateException("Error parsing GBK file " + filename + " at line " + line_num + " (" + t.getMessage() + ")", t);
        }
        if ((loc != null) && (loc.isClosed())) loc.close(filename);
        if (seq != null) seq.close(filename);
    }

    /**
     * @param args
     * @throws Exception
     */
    public static void main(String[] args) throws Exception {
        final PrintWriter pw = new PrintWriter("test/parse.txt");
        final String filename = "Pseudomonas_stutzeri_DSM_10701.gb";
        BufferedReader br = new BufferedReader(new FileReader(new File("test/" + filename)));
        parse(br, new GbkParsingParams(false), filename, new GbkCallback() {
            @Override
            public void setGenomeTrackFile(String contigName, String genomeName, int taxId, String plasmid, String filename) throws Exception {
                pw.println("setGenome: contigName=" + contigName + ", genomeName=" + genomeName + ", taxId=" + taxId + ", plasmid=" + plasmid);
            }

            @Override
            public void addHeaderTrackFile(String contigName, String headerType, String value, List<GbkSubheader> items, String filename) throws Exception {
                pw.println("addHeader: contigName=" + contigName + ", type=" + headerType + ", value=" + value + ", subheader=" + items);
            }

            @Override
            public void addFeatureTrackFile(String contigName, String featureType, int strand, int start, int stop, List<GbkLocation> locations, List<GbkQualifier> props, String filename) throws Exception {
                pw.println("addFeature: contigName=" + contigName + ", type=" + featureType + ", " +
                        "start=" + start + ", stop=" + stop + ", strand=" + strand + ", locations=" + locations + ", props=" + props);
            }

            @Override
            public void addSeqPartTrackFile(String contigName, int seqPartIndex, String seqPart, int commonLen, String filename) {
                pw.println("addSeqPart: contigName=" + contigName + ", seqPartIndex=" + seqPartIndex +
                        ", seqPart=" + seqPart.length());
            }
        });
        br.close();
        pw.close();
    }
}
