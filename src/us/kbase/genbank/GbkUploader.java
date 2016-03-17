package us.kbase.genbank;

import us.kbase.auth.AuthToken;
import us.kbase.common.service.Tuple11;
import us.kbase.common.service.Tuple3;
import us.kbase.common.service.Tuple4;
import us.kbase.common.service.UObject;
import us.kbase.kbasegenomes.Contig;
import us.kbase.kbasegenomes.ContigSet;
import us.kbase.kbasegenomes.Feature;
import us.kbase.kbasegenomes.Genome;
import us.kbase.workspace.*;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.net.URL;
import java.util.*;

public class GbkUploader {


    final static boolean debug = false;
    public final static String[] domains = {"bacteria", "archaea", "eukarya", "eukaryota", "viruses"};

    /**
     * @param files
     * @param wsName
     * @param id
     * @throws Exception
     */
    public static ArrayList uploadGbk(List<File> files, String wsName, String id) {

        ArrayList ar = null;
        try {
            ar = (ArrayList) uploadGbk(files, wsName, id, true);
        } catch (Exception e) {
            System.out.println("uploadGbk");
            System.out.print(e.getMessage());
            System.out.print(e.getStackTrace());
            e.printStackTrace();
        }

        return ar;
    }

    /**
     * @param files
     * @param wsUrl
     * @param wsName
     * @param id
     * @param token
     * @throws Exception
     */
    public static ArrayList uploadGbk(List<File> files, String wsUrl, String wsName, String id, String token) throws Exception {
        final WorkspaceClient wc = new WorkspaceClient(new URL(wsUrl), new AuthToken(token));
        wc.setAuthAllowedForHttp(true);
        ArrayList ar = (ArrayList) uploadGbk(files, new ObjectStorage() {

            @Override
            public List<Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>>> saveObjects(
                    String authToken, SaveObjectsParams params) throws Exception {
                return wc.saveObjects(params);
            }

            @Override
            public List<ObjectData> getObjects(String authToken,
                                               List<ObjectIdentity> objectIds) throws Exception {
                return wc.getObjects(objectIds);
            }
        }, wsName, id, token, null);

        return ar;
    }


    /**
     * @param files
     * @param ws
     * @param id
     * @param doStderr
     * @return
     * @throws Exception
     */
    //  ArrayList ar = GbkUploader.uploadGbk(gbkFiles, wsname, dir.getName(), true);
    public static ArrayList uploadGbk(List<File> files, String ws, String id, boolean doStderr) throws Exception {

        boolean tmptooBig = false;

        final Map<String, Contig> contigMap = new LinkedHashMap<String, Contig>();
        final Genome genome = new Genome()
                .withComplete(1L).withDomain("").withGeneticCode(0L).withId(id)
                .withSource("KBase user upload").withSourceId(id);
        final List<Feature> features = new ArrayList<Feature>();
        final Set<String> usedFeatureIds = new HashSet<String>();
        final Map<String, Integer> generatedFeatureIds = new HashMap<String, Integer>();
        final Map<String, String> contigToOrgName = new HashMap<String, String>();
        final Map<String, String> contigToTaxonomy = new HashMap<String, String>();
        final Map<String, Boolean> contigToPlasmid = new HashMap<String, Boolean>();
        for (final File f : files) {
            double bytes = f.length();
            double kilobytes = (bytes / 1024);
            double megabytes = (kilobytes / 1024);

            if (megabytes > 1000) {
                System.err.println("WARNING GenBank file size may be above KBase upload limit");
                tmptooBig = true;
            }

            final boolean tooBig = tmptooBig;

            BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(f)));
            try {
                GbkParser.parse(br, new GbkParsingParams(true), f.getName(), new GbkCallback() {
                    @Override
                    public void setGenomeTrackFile(String contigName, String genomeName, int taxId, String plasmid, String filename) {
                        try {
                            if (contigToOrgName.get(contigName) == null)
                                contigToOrgName.put(contigName, genomeName);
                            genome.getAdditionalProperties().put("tax_id", taxId);
                            //genome.setSourceId(taxId);
                            contigToPlasmid.put(contigName, plasmid != null);
                        } catch (Exception e) {
                            System.err.println("setGenome");
                            System.err.print(e.getMessage());
                            System.err.print(e.getStackTrace());
                            e.printStackTrace();
                        }
                    }

                    @Override
                    public void addSeqPartTrackFile(String contigName, int seqPartIndex, String seqPart,
                                                    int commonLen, String filename) {
                        try {
                            Contig contig = contigMap.get(contigName);
                            if (contig == null) {
                                contig = new Contig().withId(contigName).withName(contigName).withMd5("md5")
                                        .withSequence("");
                                contigMap.put(contigName, contig);
                            }
                            //only add sequence if input file was not too big
                            if (!tooBig) {
                                contig.withSequence(contig.getSequence() + seqPart);
                            }
                        } catch (Exception e) {
                            System.err.println("addSeqPart");
                            System.err.print(e.getMessage());
                            System.err.print(e.getStackTrace());
                            e.printStackTrace();
                        }
                    }

                    @Override
                    public void addHeaderTrackFile(String contigName, String headerType, String value,
                                                   List<GbkSubheader> items, String filename) {
                        try {
                            if (headerType.equals("SOURCE")) {
                                String genomeName = value;
                                //genome.withScientificName(genomeName);
                                contigToOrgName.put(contigName, genomeName);
                                for (GbkSubheader sub : items) {
                                    if (sub.type.equals("ORGANISM")) {
                                        String taxPath = sub.getValue();
                                        String[] parts = taxPath.split("\n");
                                        taxPath = "";
                                        for (int i = 0; i < parts.length; i++) {
                                            if (i == 0 && parts[0].equals(genomeName))
                                                continue;
                                            if (taxPath.length() > 0)
                                                taxPath += " ";
                                            taxPath += parts[i];
                                        }
                                        if (taxPath.endsWith("."))
                                            taxPath = taxPath.substring(0, taxPath.length() - 1).trim();
                                        String fullPath = taxPath + "; " + genomeName;
                                        contigToTaxonomy.put(contigName, fullPath);
                                    }
                                }
                            }
                        } catch (Exception e) {
                            System.err.println("SOURCE, ORGANISM");
                            System.err.print(e.getMessage());
                            System.err.print(e.getStackTrace());
                            e.printStackTrace();
                        }
                    }

                    @Override
                    public void addFeatureTrackFile(String contigName, String featureType, int strand,
                                                    int start, int stop, List<GbkLocation> locations,
                                                    List<GbkQualifier> props, String filename) {
                        try {
                            Feature f = null;
                            if (featureType.equals("CDS")) {
                                f = new Feature().withType("CDS");
                            } else if (featureType.toUpperCase().endsWith("RNA")) {
                                f = new Feature().withType("RNA");
                            }
                            if (f == null)
                                return;
                            List<Tuple4<String, Long, String, Long>> locList = new ArrayList<Tuple4<String, Long, String, Long>>();
                            for (GbkLocation loc : locations) {
                                long realStart = loc.strand > 0 ? loc.start : loc.stop;
                                String dir = loc.strand > 0 ? "+" : "-";
                                long len = loc.stop + 1 - loc.start;
                                locList.add(new Tuple4<String, Long, String, Long>().withE1(contigName)
                                        .withE2(realStart).withE3(dir).withE4(len));
                            }

                            f.withLocation(locList).withAnnotations(new ArrayList<Tuple3<String, String, Long>>());
                            f.withAliases(new ArrayList<String>());
                            for (GbkQualifier prop : props) {
                                if (debug)
                                    System.out.println("addFeatureTrackFile " + prop.type);
                                if (prop.type.equalsIgnoreCase("locus_tag")) {
                                    try {
                                        f.setId(prop.getValue());
                                    } catch (Exception e) {
                                        System.err.println("locus_tag error " + filename);
                                        System.err.print(e.getMessage());
                                        System.err.print(e.getStackTrace());
                                        e.printStackTrace();
                                    }
                                } else if (prop.type.equalsIgnoreCase("translation")) {
                                    try {
                                        String seq = prop.getValue();
                                        f.withProteinTranslation(seq).withProteinTranslationLength((long) seq.length());
                                    } catch (Exception e) {
                                        System.err.println("translation error " + filename);
                                        System.err.print(e.getMessage());
                                        System.err.print(e.getStackTrace());
                                        e.printStackTrace();
                                    }
                                } /*else if (prop.type.equals("note")) {
                                    try {
                                        f.setFunction(prop.getValue());
                                    } catch (Exception e) {
                                        System.err.println("note error " + filename);
                                        System.err.print(e.getMessage());
                                        System.err.print(e.getStackTrace());
                                        e.printStackTrace();
                                    }
                                }*/
                                //use function field if has info
                                else if (prop.type.equalsIgnoreCase("function")) {
                                    try {
                                        if (prop.getValue() != null && prop.getValue().length() > 0)
                                            f.setFunction(prop.getValue());
                                    } catch (Exception e) {
                                        System.err.println("note error " + filename);
                                        System.err.print(e.getMessage());
                                        System.err.print(e.getStackTrace());
                                        e.printStackTrace();
                                    }
                                }
                                //only use product field if function field is empty
                                else if (prop.type.equalsIgnoreCase("product")) {
                                    try {
                                        if (f.getFunction() == null || f.getFunction().length() == 0)
                                            f.setFunction(prop.getValue());
                                    } catch (Exception e) {
                                        System.err.println("product error " + filename);
                                        System.err.print(e.getMessage());
                                        System.err.print(e.getStackTrace());
                                        e.printStackTrace();
                                    }
                                } else if (prop.type.equalsIgnoreCase("gene")) {
                                    try {
                                        final String pg = prop.getValue();
                                        //System.out.println("addFeatureTrackFile gene "+pg);
                                        if (f.getId() == null) {
                                            f.setId(pg);
                                        }
                                        f.getAliases().add(pg);
                                    } catch (Exception e) {
                                        System.err.println("gene error " + filename);
                                        System.err.print(e.getMessage());
                                        System.err.print(e.getStackTrace());
                                        e.printStackTrace();
                                    }
                                } else if (prop.type.equalsIgnoreCase("protein_id")) {
                                    try {
                                        final String pg = prop.getValue();
                                        ArrayList aliases = (ArrayList) f.getAliases();

                                        if (debug) {
                                            System.out.println("getAliases");
                                            System.out.println(aliases);
                                        }

                                        if (!aliases.contains(pg))
                                            f.getAliases().add(pg);
                                    } catch (Exception e) {
                                        System.err.println("add alias error " + filename);
                                        System.err.print(e.getMessage());
                                        System.err.print(e.getStackTrace());
                                        e.printStackTrace();
                                    }
                                } else if (prop.type.equalsIgnoreCase("db_xref")) {//protein id
                                    try {
                                        final String pg = prop.getValue();
                                        ArrayList aliases = (ArrayList) f.getAliases();

                                        if (debug) {
                                            System.out.println("getAliases");
                                            System.out.println(aliases);
                                        }

                                        if (!aliases.contains(pg))
                                            f.getAliases().add(pg);
                                    } catch (Exception e) {
                                        System.err.println("add alias error " + filename);
                                        System.err.print(e.getMessage());
                                        System.err.print(e.getStackTrace());
                                        e.printStackTrace();
                                    }
                                }
                            }
                            if (f.getId() == null) {
                                Integer last = generatedFeatureIds.get(f.getType());
                                if (last == null)
                                    last = 0;
                                last++;
                                f.setId(f.getType() + "." + last);
                                generatedFeatureIds.put(f.getType(), last);
                            }
                            features.add(f);
                            usedFeatureIds.add(f.getId());
                        } catch (Exception e) {
                            System.err.println("addFeature error " + filename);
                            System.err.print(e.getMessage());
                            System.err.print(e.getStackTrace());
                            e.printStackTrace();
                        }
                    }
                });
            } finally {
                br.close();
            }
        }
        // Process all non-plasmids first
        try {
            boolean nameProblems = false;
            for (String key : contigToOrgName.keySet()) {
                Boolean isPlasmid = contigToPlasmid.get(key);
                if (isPlasmid != null && isPlasmid)
                    continue;
                genome.setScientificName(contigToOrgName.get(key));
                String taxonomy = contigToTaxonomy.get(key);
                //System.out.println("taxonomy "+taxonomy);

                String domain = taxonomy.substring(0, taxonomy.indexOf(";"));
                //System.out.println("domain "+domain);

                if (taxonomy != null) {
                    if (genome.getTaxonomy() != null && !genome.getTaxonomy().equals(taxonomy)) {
                        System.err.println("Taxonomy path is wrong in file [" + files.get(0).getParent() + ":" +
                                key + "]: " + taxonomy);
                        System.err.println("is different from '" + genome.getTaxonomy() + "')");
                        nameProblems = true;
                    }
                    //System.out.println("nonplasmid genome.withTaxonomy(taxonomy) 1 " + taxonomy);
                    if (Arrays.asList(domains).contains(domain.toLowerCase()))
                        genome.withTaxonomy(taxonomy).withDomain(domain);
                    else {
                        System.err.println("Domain not recognized " + domain);
                        genome.withTaxonomy(taxonomy).withDomain(domain);
                    }
                } else
                    genome.withTaxonomy("").withDomain("");
            }
        } catch (Exception e) {
            System.err.println("non plamids");
            System.err.print(e.getMessage());
            System.err.print(e.getStackTrace());
            e.printStackTrace();
        }
        try {
            // And all plasmids now
            for (String key : contigToOrgName.keySet()) {
                Boolean isPlasmid = contigToPlasmid.get(key);
                if (isPlasmid != null && !isPlasmid)
                    continue;
                if (genome.getScientificName() == null)
                    genome.setScientificName(contigToOrgName.get(key));
                String taxonomy = contigToTaxonomy.get(key);
                String domain = taxonomy.substring(0, taxonomy.indexOf(";"));
                if (genome.getTaxonomy() == null && taxonomy != null) {
                    if (Arrays.asList(domains).contains(domain.toLowerCase()))
                        //System.out.println("plasmid genome.withTaxonomy(taxonomy) 1 " + taxonomy);
                        genome.withTaxonomy(taxonomy).withDomain(domain);
                    else {
                        System.err.println("Domain not recognized " + domain);
                        genome.withTaxonomy(taxonomy).withDomain("");
                    }
                } else
                    genome.withTaxonomy("").withDomain("");
            }
        } catch (Exception e) {
            System.err.println("plamids");
            System.err.print(e.getMessage());
            System.err.print(e.getStackTrace());
            e.printStackTrace();
        }


        String contigSetId = null;
        ContigSet contigSet = null;
        try {
            if (contigMap.size() == 0) {
                System.err.println("GBK file has no DNA-sequence");
                //throw new Exception("GBK-file has no DNA-sequence");
            }
            contigSetId = id + ".contigset";
            List<Long> contigLengths = new ArrayList<Long>();
            long dnaLen = 0;
            for (Contig contig : contigMap.values()) {
                if (contig.getSequence() == null || contig.getSequence().length() == 0) {
                    throw new Exception("Contig " + contig.getId() + " has no DNA-sequence");
                }
                contig.withLength((long) contig.getSequence().length());
                contigLengths.add(contig.getLength());
                dnaLen += contig.getLength();
            }
            contigSet = new ContigSet().withContigs(new ArrayList<Contig>(contigMap.values()))
                    .withId(contigSetId).withMd5("md5").withName(id)
                    .withSource("User uploaded data").withSourceId(id).withType("Organism");

            long numcontig = 0;
            if (contigMap != null) {
                if (contigMap.keySet() != null && contigMap.keySet().size() > 0) {
                    numcontig = (long) contigMap.keySet().size();
                }
            }
            if (ws != null) {
                String ctgRef = ws + "/" + contigSetId;
                genome.withContigIds(new ArrayList<String>(contigMap.keySet())).withNumContigs(numcontig).withContigLengths(contigLengths)
                        .withDnaSize(dnaLen).withContigsetRef(ctgRef).withFeatures(features)
                        .withGcContent(calculateGcContent(contigSet));
            } else {
                genome.withContigIds(new ArrayList<String>(contigMap.keySet())).withNumContigs(numcontig).withContigLengths(contigLengths)
                        .withDnaSize(dnaLen).withFeatures(features)
                        .withGcContent(calculateGcContent(contigSet));
            }
        } catch (Exception e) {
            System.err.println("contigs");
            System.err.print(e.getMessage());
            System.err.print(e.getStackTrace());
            e.printStackTrace();
        }

        Map<String, String> meta = new LinkedHashMap<String, String>();
        meta.put("Scientific name", genome.getScientificName());

        ArrayList ar = new ArrayList();
        ar.add(ws);
        ar.add(id);
        ar.add(genome);
        ar.add(contigSetId);
        ar.add(contigSet);
        ar.add(meta);

        return ar;

    }


    /**
     * @param files
     * @param wc
     * @param ws
     * @param id
     * @param token
     * @param genomeNameToPaths
     * @throws Exception
     */
    public static ArrayList uploadGbk(List<File> files, ObjectStorage wc, String ws, String id, String token,
                                      Map<String, List<String>> genomeNameToPaths) throws Exception {
        final Map<String, Contig> contigMap = new LinkedHashMap<String, Contig>();
        final Genome genome = new Genome()
                .withComplete(1L).withDomain("").withGeneticCode(0L).withId(id)
                .withSource("KBase user upload").withSourceId(id);
        final List<Feature> features = new ArrayList<Feature>();
        final Set<String> usedFeatureIds = new HashSet<String>();
        final Map<String, Integer> generatedFeatureIds = new HashMap<String, Integer>();
        final Map<String, String> contigToOrgName = new HashMap<String, String>();
        final Map<String, String> contigToTaxonomy = new HashMap<String, String>();
        final Map<String, Boolean> contigToPlasmid = new HashMap<String, Boolean>();
        for (final File f : files) {
            BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(f)));
            try {
                GbkParser.parse(br, new GbkParsingParams(true), f.getName(), new GbkCallback() {
                    @Override
                    public void setGenomeTrackFile(String contigName, String genomeName, int taxId, String plasmid, String filename) throws Exception {
                        if (contigToOrgName.get(contigName) == null)
                            contigToOrgName.put(contigName, genomeName);
                        genome.getAdditionalProperties().put("tax_id", taxId);
                        contigToPlasmid.put(contigName, plasmid != null);
                    }

                    @Override
                    public void addSeqPartTrackFile(String contigName, int seqPartIndex, String seqPart,
                                                    int commonLen, String filename) throws Exception {
                        Contig contig = contigMap.get(contigName);
                        if (contig == null) {
                            contig = new Contig().withId(contigName).withName(contigName).withMd5("md5")
                                    .withSequence("");
                            contigMap.put(contigName, contig);
                        }
                        contig.withSequence(contig.getSequence() + seqPart);
                    }

                    @Override
                    public void addHeaderTrackFile(String contigName, String headerType, String value,
                                                   List<GbkSubheader> items, String filename) throws Exception {
                        if (headerType.equals("SOURCE")) {
                            String genomeName = value;
                            //genome.withScientificName(genomeName);
                            contigToOrgName.put(contigName, genomeName);
                            for (GbkSubheader sub : items) {
                                if (sub.type.equals("ORGANISM")) {
                                    String taxPath = sub.getValue();
                                    String[] parts = taxPath.split("\n");
                                    taxPath = "";
                                    for (int i = 0; i < parts.length; i++) {
                                        if (i == 0 && parts[0].equals(genomeName))
                                            continue;
                                        if (taxPath.length() > 0)
                                            taxPath += " ";
                                        taxPath += parts[i];
                                    }
                                    if (taxPath.endsWith("."))
                                        taxPath = taxPath.substring(0, taxPath.length() - 1).trim();
                                    String fullPath = taxPath + "; " + genomeName;
                                    contigToTaxonomy.put(contigName, fullPath);
                                }
                            }
                        }
                    }

                    @Override
                    public void addFeatureTrackFile(String contigName, String featureType, int strand,
                                                    int start, int stop, List<GbkLocation> locations,
                                                    List<GbkQualifier> props, String filename) throws Exception {
                        Feature f = null;
                        if (featureType.equals("CDS")) {
                            f = new Feature().withType("CDS");
                        } else if (featureType.toUpperCase().endsWith("RNA")) {
                            f = new Feature().withType("RNA");
                        }
                        if (f == null)
                            return;
                        List<Tuple4<String, Long, String, Long>> locList = new ArrayList<Tuple4<String, Long, String, Long>>();
                        for (GbkLocation loc : locations) {
                            long realStart = loc.strand > 0 ? loc.start : loc.stop;
                            String dir = loc.strand > 0 ? "+" : "-";
                            long len = loc.stop + 1 - loc.start;
                            locList.add(new Tuple4<String, Long, String, Long>().withE1(contigName)
                                    .withE2(realStart).withE3(dir).withE4(len));
                        }
                        f.withLocation(locList).withAnnotations(new ArrayList<Tuple3<String, String, Long>>());
                        f.withAliases(new ArrayList<String>());
                        for (GbkQualifier prop : props) {
                            if (prop.type.equals("locus_tag")) {
                                f.setId(prop.getValue());
                            } else if (prop.type.equals("translation")) {
                                String seq = prop.getValue();
                                f.withProteinTranslation(seq).withProteinTranslationLength((long) seq.length());
                            } else if (prop.type.equals("note")) {
                                f.setFunction(prop.getValue());
                            } else if (prop.type.equals("product")) {
                                if (f.getFunction() == null)
                                    f.setFunction(prop.getValue());
                            } else if (prop.type.equals("gene")) {
                                final String pg = prop.getValue();
                                if (f.getId() == null) {
                                    f.setId(pg);
                                }
                                //System.out.println("addFeatureTrackFile "+pg);

                                ArrayList aliases = (ArrayList) f.getAliases();

                                if (debug) {
                                    System.out.println("getAliases");
                                    System.out.println(aliases);
                                }

                                if (!aliases.contains(pg))
                                    f.getAliases().add(pg);

                            } else if (prop.type.equals("protein_id")) {
                                ArrayList aliases = (ArrayList) f.getAliases();

                                if (debug) {
                                    System.out.println("getAliases");
                                    System.out.println(aliases);
                                }
                                String val = prop.getValue();
                                if (!aliases.contains(val))
                                    f.getAliases().add(val);
                            }
                        }
                        if (f.getId() == null) {
                            Integer last = generatedFeatureIds.get(f.getType());
                            if (last == null)
                                last = 0;
                            last++;
                            f.setId(f.getType() + "." + last);
                            generatedFeatureIds.put(f.getType(), last);
                        }
                        features.add(f);
                        usedFeatureIds.add(f.getId());
                    }
                });
            } finally {
                br.close();
            }
        }
        // Process all non-plasmids first
        boolean nameProblems = false;
        for (String key : contigToOrgName.keySet()) {
            Boolean isPlasmid = contigToPlasmid.get(key);
            if (isPlasmid != null && isPlasmid)
                continue;
            genome.setScientificName(contigToOrgName.get(key));
            String taxonomy = contigToTaxonomy.get(key);
            String domain = taxonomy.substring(0, taxonomy.indexOf(";"));
            if (taxonomy != null) {
                if (genome.getTaxonomy() != null && !genome.getTaxonomy().equals(taxonomy)) {
                    System.err.println("Taxonomy path is wrong in file [" + files.get(0).getParent() + ":" +
                            key + "]: " + taxonomy + " (it's different from '" + genome.getTaxonomy() + "')");
                    nameProblems = true;
                }
                //System.out.println("nonplasmid genome.withTaxonomy(taxonomy) 1 " + taxonomy);
                if (Arrays.asList(domains).contains(domain.toLowerCase()))
                    genome.withTaxonomy(taxonomy).withDomain(domain);
                else {
                    System.err.println("Domain not recognized " + domain);
                    genome.withTaxonomy(taxonomy).withDomain("");
                }
            }
            genome.withTaxonomy("").withDomain("");
        }
        // And all plasmids now
        for (String key : contigToOrgName.keySet()) {
            Boolean isPlasmid = contigToPlasmid.get(key);
            if (isPlasmid != null && !isPlasmid)
                continue;
            if (genome.getScientificName() == null)
                genome.setScientificName(contigToOrgName.get(key));
            String taxonomy = contigToTaxonomy.get(key);
            String domain = taxonomy.substring(0, taxonomy.indexOf(";"));
            if (genome.getTaxonomy() == null && taxonomy != null) {
                //System.out.println("plasmid genome.withTaxonomy(taxonomy) 1 " + taxonomy);
                if (Arrays.asList(domains).contains(domain.toLowerCase()))
                    genome.withTaxonomy(taxonomy).withDomain(domain);
                else {
                    System.err.println("Domain not recognized " + domain);
                    genome.withTaxonomy(taxonomy).withDomain("");
                }
            } else
                genome.withTaxonomy("").withDomain("");
        }
        if (contigMap.size() == 0) {
            throw new Exception("GBK-file has no DNA-sequence");
        }
        if (genomeNameToPaths != null && !nameProblems) {
            List<String> paths = new ArrayList<String>();
            for (File f : files)
                paths.add(f.getParentFile().getName() + "/" + f.getName());
            genomeNameToPaths.put(genome.getScientificName(), paths);
        }
        String contigId = id + ".contigset";
        List<Long> contigLengths = new ArrayList<Long>();
        long dnaLen = 0;
        for (Contig contig : contigMap.values()) {
            if (contig.getSequence() == null || contig.getSequence().length() == 0) {
                throw new Exception("Contig " + contig.getId() + " has no DNA-sequence");
            }
            contig.withLength((long) contig.getSequence().length());
            contigLengths.add(contig.getLength());
            dnaLen += contig.getLength();
        }
        ContigSet contigSet = new ContigSet().withContigs(new ArrayList<Contig>(contigMap.values()))
                .withId(id).withMd5("md5").withName(id)
                .withSource("User uploaded data").withSourceId("USER").withType("Organism");
          /*  wc.saveObjects(token, new SaveObjectsParams().withWorkspace(ws)
                    .withObjects(Arrays.asList(new ObjectSaveData().withName(contigId)
                            .withType("KBaseGenomes.ContigSet").withData(new UObject(contigSet)))));*/
        String ctgRef = ws + "/" + contigId;

        int numcontig = 0;
        if (contigMap != null)
            if (contigMap.keySet() != null)
                numcontig = contigMap.keySet().size();

        genome.withContigIds(new ArrayList<String>(contigMap.keySet())).withNumContigs((long) numcontig).withContigLengths(contigLengths)
                .withDnaSize(dnaLen).withContigsetRef(ctgRef).withFeatures(features)
                .withGcContent(calculateGcContent(contigSet));
        genome.withSourceId(genome.getId());

        Map<String, String> meta = new LinkedHashMap<String, String>();
        meta.put("Scientific name", genome.getScientificName());
            /*wc.saveObjects(token, new SaveObjectsParams().withWorkspace(ws)
                    .withObjects(Arrays.asList(new ObjectSaveData().withName(id).withMeta(meta)
                            .withType("KBaseGenomes.Genome").withData(new UObject(genome)))));*/

        GbkUploader.uploadtoWS(wc, ws, id, token, genome, contigId, contigSet, meta);
        ArrayList ar = new ArrayList();
        ar.add(wc);
        ar.add(ws);
        ar.add(id);
        ar.add(token);
        ar.add(genome);
        ar.add(contigId);
        ar.add(contigSet);
        ar.add(meta);

        return ar;
    }


    /**
     * @param wc
     * @param ws
     * @param id
     * @param token
     * @param genome
     * @param contigId
     * @param contigSet
     * @param meta
     * @throws Exception
     */
    public final static void uploadtoWS(ObjectStorage wc, String ws, String id, String token, Genome genome, String contigId, ContigSet contigSet, Map<String, String> meta) {
        try {
            wc.saveObjects(token, new SaveObjectsParams().withWorkspace(ws)
                    .withObjects(Arrays.asList(new ObjectSaveData().withName(contigId)
                            .withType("KBaseGenomes.ContigSet").withData(new UObject(contigSet)))));
            System.out.println("uploadtoWS upload ContigSet");
        } catch (Exception e) {
            System.err.println("upload ContigSet");
            System.err.print(e.getMessage());
            System.err.print(e.getStackTrace());
            e.printStackTrace();
        }

        try {
            wc.saveObjects(token, new SaveObjectsParams().withWorkspace(ws)
                    .withObjects(Arrays.asList(new ObjectSaveData().withName(id).withMeta(meta)
                            .withType("KBaseGenomes.Genome").withData(new UObject(genome)))));
            System.out.println("uploadtoWS upload ContigSet");
        } catch (Exception e) {
            System.err.println("upload Genome");
            System.err.print(e.getMessage());
            System.err.print(e.getStackTrace());
            e.printStackTrace();
        }
    }

    /**
     * @param contigs
     * @return
     */
    public static double calculateGcContent(ContigSet contigs) {
        int at = 0;
        int gc = 0;
        for (Contig contig : contigs.getContigs()) {
            String seq = contig.getSequence();
            for (int i = 0; i < seq.length(); i++) {
                char ch = seq.charAt(i);
                if (ch == 'g' || ch == 'G' || ch == 'c' || ch == 'C') {
                    gc++;
                } else if (ch == 'a' || ch == 'A' || ch == 't' || ch == 'T') {
                    at++;
                }
            }
        }
        return (0.0 + gc) / (at + gc);
    }
}
