package us.kbase.genbank;

import us.kbase.auth.AuthToken;
import us.kbase.auth.TokenFormatException;
import us.kbase.common.service.Tuple3;
import us.kbase.common.service.Tuple4;
import us.kbase.common.service.UObject;
import us.kbase.common.service.UnauthorizedException;
import us.kbase.kbasegenomes.Contig;
import us.kbase.kbasegenomes.ContigSet;
import us.kbase.kbasegenomes.Feature;
import us.kbase.kbasegenomes.Genome;
import us.kbase.workspace.ObjectSaveData;
import us.kbase.workspace.SaveObjectsParams;
import us.kbase.workspace.WorkspaceClient;

import java.io.*;
import java.net.URL;
import java.util.*;

public class GbkUploader {

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
            System.err.println("uploadGbk");
            System.err.print(e.getMessage());
            System.err.print(e.getStackTrace());
            e.printStackTrace();
        }

        return ar;
    }


    /**
     *
     * @param files
     * @param ws
     * @param id
     * @param doStderr
     * @return
     * @throws Exception
     */
    public static ArrayList uploadGbk(List<File> files, String ws, String id, boolean doStderr) throws Exception {
        final Map<String, Contig> contigMap = new LinkedHashMap<String, Contig>();
        final Genome genome = new Genome()
                .withComplete(1L).withDomain("Bacteria").withGeneticCode(11L).withId(id)
                .withNumContigs(1L).withSource("NCBI").withSourceId("NCBI");
        final List<Feature> features = new ArrayList<Feature>();
        final Set<String> usedFeatureIds = new HashSet<String>();
        final Map<String, Integer> generatedFeatureIds = new HashMap<String, Integer>();
        final Map<String, String> contigToOrgName = new HashMap<String, String>();
        final Map<String, String> contigToTaxonomy = new HashMap<String, String>();
        final Map<String, Boolean> contigToPlasmid = new HashMap<String, Boolean>();
        for (final File f : files) {
            BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(f)));
            try {
                GbkParser.parse(br, new GbkParsingParams(true), new GbkCallback() {
                    @Override
                    public void setGenome(String contigName, String genomeName, int taxId, String plasmid) {
                        try {
                            if (contigToOrgName.get(contigName) == null)
                                contigToOrgName.put(contigName, genomeName);
                            genome.getAdditionalProperties().put("tax_id", taxId);
                            contigToPlasmid.put(contigName, plasmid != null);
                        } catch (Exception e) {
                            System.err.println("setGenome");
                            System.err.print(e.getMessage());
                            System.err.print(e.getStackTrace());
                            e.printStackTrace();
                        }
                    }

                    @Override
                    public void addSeqPart(String contigName, int seqPartIndex, String seqPart,
                                           int commonLen) {
                        try {
                            Contig contig = contigMap.get(contigName);
                            if (contig == null) {
                                contig = new Contig().withId(contigName).withName(contigName).withMd5("md5")
                                        .withSequence("");
                                contigMap.put(contigName, contig);
                            }
                            contig.withSequence(contig.getSequence() + seqPart);
                        } catch (Exception e) {
                            System.err.println("addSeqPart");
                            System.err.print(e.getMessage());
                            System.err.print(e.getStackTrace());
                            e.printStackTrace();
                        }
                    }

                    @Override
                    public void addHeader(String contigName, String headerType, String value,
                                          List<GbkSubheader> items) {
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
                    public void addFeature(String contigName, String featureType, int strand,
                                           int start, int stop, List<GbkLocation> locations,
                                           List<GbkQualifier> props) {
                        try {
                            Feature f = null;
                            if (featureType.equals("CDS")) {
                                f = new Feature().withType("CDS");
                            } else if (featureType.toUpperCase().endsWith("RNA")) {
                                f = new Feature().withType("rna");
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
                                    try {
                                        f.setId(prop.getValue());
                                    } catch (Exception e) {
                                        System.err.println("locus_tag");
                                        System.err.print(e.getMessage());
                                        System.err.print(e.getStackTrace());
                                        e.printStackTrace();
                                    }
                                } else if (prop.type.equals("translation")) {
                                    try {
                                        String seq = prop.getValue();
                                        f.withProteinTranslation(seq).withProteinTranslationLength((long) seq.length());
                                    } catch (Exception e) {
                                        System.err.println("translation");
                                        System.err.print(e.getMessage());
                                        System.err.print(e.getStackTrace());
                                        e.printStackTrace();
                                    }
                                } else if (prop.type.equals("note")) {
                                    try {
                                        f.setFunction(prop.getValue());
                                    } catch (Exception e) {
                                        System.err.println("note");
                                        System.err.print(e.getMessage());
                                        System.err.print(e.getStackTrace());
                                        e.printStackTrace();
                                    }
                                } else if (prop.type.equals("product")) {
                                    try {
                                        if (f.getFunction() == null)
                                            f.setFunction(prop.getValue());
                                    } catch (Exception e) {
                                        System.err.println("product");
                                        System.err.print(e.getMessage());
                                        System.err.print(e.getStackTrace());
                                        e.printStackTrace();
                                    }
                                } else if (prop.type.equals("gene")) {
                                    try {
                                        if (f.getId() == null)
                                            f.setId(prop.getValue());
                                        f.getAliases().add(prop.getValue());
                                    } catch (Exception e) {
                                        System.err.println("gene");
                                        System.err.print(e.getMessage());
                                        System.err.print(e.getStackTrace());
                                        e.printStackTrace();
                                    }
                                } else if (prop.type.equals("protein_id")) {
                                    try {
                                        f.getAliases().add(prop.getValue());
                                    } catch (Exception e) {
                                        System.err.println("addFeature");
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
                            System.err.println("addFeature");
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
                if (taxonomy != null) {
                    if (genome.getTaxonomy() != null && !genome.getTaxonomy().equals(taxonomy)) {
                        System.err.println("Taxonomy path is wrong in file [" + files.get(0).getParent() + ":" +
                                key + "]: " + taxonomy + " (it's different from '" + genome.getTaxonomy() + "')");
                        nameProblems = true;
                    }
                    genome.withTaxonomy(taxonomy);
                }
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
                if (genome.getTaxonomy() == null && taxonomy != null)
                    genome.withTaxonomy(taxonomy);
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
                System.err.println("GBK-file has no DNA-sequence");
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
                    .withSource("User uploaded data").withSourceId("USER").withType("Organism");

            if (ws != null) {
                String ctgRef = ws + "/" + contigSetId;
                genome.withContigIds(new ArrayList<String>(contigMap.keySet())).withContigLengths(contigLengths)
                        .withDnaSize(dnaLen).withContigsetRef(ctgRef).withFeatures(features)
                        .withGcContent(calculateGcContent(contigSet));
            } else {
                genome.withContigIds(new ArrayList<String>(contigMap.keySet())).withContigLengths(contigLengths)
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
