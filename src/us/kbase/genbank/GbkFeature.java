package us.kbase.genbank;

import java.util.ArrayList;
import java.util.List;
import java.util.StringTokenizer;

/**
 * Parsing of contig features (GbkParser).
 * Features can be genes, proteins, rna. Eveny
 * feature has a set of intervals (GbkLocation).
 *
 * @author rsutormin
 */
public class GbkFeature extends GbkLocation {
    public static final String TAXON_PREFIX = "taxon:";
    public static final String DBXREF_PREFIX = "db_xref:";
    public List<GbkLocation> locations;
    public List<GbkQualifier> qualifiers;
    public boolean wasError = false;

    public GbkFeature(int line_num, String type, String value) {
        super(line_num, type, value);
        this.qualifiers = new ArrayList<GbkQualifier>();
        this.locations = new ArrayList<GbkLocation>();
    }

    public void close(GbkParsingParams params) {
        String val = value.toString();
        int str = 1;
        if ((val.startsWith("complement(")) && (val.endsWith(")"))) {
            str = -1;
            val = val.substring(11, val.length() - 1).trim();
        }
        if ((val.startsWith("join(")) && (val.endsWith(")"))) {
            val = val.substring(5, val.length() - 1).trim();
        }
        if ((val.startsWith("order(")) && (val.endsWith(")"))) {
            val = val.substring(6, val.length() - 1).trim();
        }
        StringTokenizer st = new StringTokenizer(val, ",");
        String error = null;
        int minStart = 0;
        int maxStop = 0;
        while (st.hasMoreTokens()) {
            String w = st.nextToken().trim();
            int pos = w.indexOf("..");
            if (pos < 0) {
                error = "Can not find [..] between start and stop";
                break;
            } else {
                try {
                    String value = w.substring(0, pos).trim();
                    if ((value.charAt(0) == '<') || (value.charAt(0) == '>')) {
                        value = value.substring(1).trim();
                    }
                    int start = Integer.parseInt(value);
                    value = w.substring(pos + 2).trim();
                    if ((value.charAt(0) == '<') || (value.charAt(0) == '>')) {
                        value = value.substring(1).trim();
                    }
                    int stop = Integer.parseInt(value);
                    if (start > stop) continue;
                    if ((locations.size() == 0) || (minStart > start))
                        minStart = start;
                    if ((locations.size() == 0) || (maxStop < stop))
                        maxStop = stop;
                    GbkLocation loc = new GbkLocation(line_num, "location", null);
                    loc.strand = str;
                    loc.start = start;
                    loc.stop = stop;
                    locations.add(loc);
                } catch (Exception ex) {
                    error = ex.getMessage();
                    break;
                }
            }
        }
        if (error != null) {
            wasError = true;
            if (!params.isIgnoreWrongFeatureLocation())
                System.out.println("Error parsing location for feature [" + type + "] on line " + line_num + ": " + error);
            return;
        }
        if (locations.size() == 0) {
            wasError = true;
            if (!params.isIgnoreWrongFeatureLocation())
                System.out.println("Error detecting location for feature [" + type + "] on line " + line_num);
            return;
        }
        this.strand = str;
        this.start = minStart;
        this.stop = maxStop;
    }

    /**
     * @param locus
     * @param ret
     * @param filename
     * @throws Exception
     */
    public void save(GbkLocus locus, GbkCallback ret, String filename) throws Exception {
        if (wasError)
            return;
        if (type.equals("source")) {
            String genomeName = null;
            int taxId = -1;
            String plasmid = null;
            ArrayList aliases = new ArrayList();
            for (GbkQualifier qualifier : qualifiers) {
                //System.out.println("qualifier " + qualifier);
                if (qualifier.type.equalsIgnoreCase("organism")) {
                    genomeName = qualifier.getValue();
                } else if (qualifier.type.equalsIgnoreCase("db_xref")) {
                    String value = qualifier.getValue();
                    if (value.startsWith(TAXON_PREFIX)) {
                        String taxstring = value.substring(TAXON_PREFIX.length()).trim();
                        int dotind = taxstring.indexOf(".");
                        if (dotind != -1)
                            taxstring = taxstring.substring(0, dotind - 1);
                        taxId = Integer.parseInt(taxstring);
                        //System.out.println("taxid " + taxId);
                    } else {
                        //System.out.println("DBXREF_PREFIX " + value);
                        String alias = value.substring(DBXREF_PREFIX.length()).trim();
                        aliases.add(alias);
                    }
                } else if (qualifier.type.equalsIgnoreCase("plasmid")) {
                    plasmid = qualifier.getValue();
                }
            }
            //System.out.println("save genomeName " + genomeName);
            ret.setGenomeTrackFile(locus.name, genomeName, taxId, plasmid, filename);
        } else {
            ret.addFeatureTrackFile(locus.name, type, strand, start, stop, locations, qualifiers, filename);
        }
        /*if (type.equals("gene")) {
            String geneName = null;
            String descr = null;
            List<String> aliases = new ArrayList<String>();
            for (GbkQualifier qualifier : qualifiers) {
                if (qualifier.type.equals("gene")) {
                    geneName = qualifier.getValue();
                } else if (qualifier.type.equals("note")) {
                    descr = qualifier.getValue();
                } else if (qualifier.type.equals("gene_synonym")) {
                    StringTokenizer st = new StringTokenizer(qualifier.getValue(), "; ");
                    while (st.hasMoreTokens()) {
                        aliases.add(st.nextToken());
                    }
                } else if (qualifier.type.equals("locus_tag")) {
                    aliases.add(qualifier.getValue());
                } else if (qualifier.type.equals("db_xref")) {
                    String value = qualifier.getValue();
                    if (value.indexOf(':') > 0)
                        value = value.substring(value.indexOf(':') + 1);
                    aliases.add(value);
                }
            }
            if (geneName == null)
                throw new IllegalStateException("Gene has no name for feature in file [" + "], line number " + line_num);
            ret.addGene(locus.name, geneName, start, stop, strand, descr, aliases.toArray(new String[aliases.size()]));
        }*/
    }
}
