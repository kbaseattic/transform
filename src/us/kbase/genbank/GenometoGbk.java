package us.kbase.genbank;

import com.fasterxml.jackson.databind.ObjectMapper;
import us.kbase.auth.AuthException;
import us.kbase.auth.AuthService;
import us.kbase.auth.AuthToken;
import us.kbase.auth.AuthUser;
import us.kbase.common.service.JsonClientException;
import us.kbase.common.service.Tuple11;
import us.kbase.common.service.Tuple4;
import us.kbase.common.service.UObject;
import us.kbase.kbasegenomes.Contig;
import us.kbase.kbasegenomes.ContigSet;
import us.kbase.kbasegenomes.Feature;
import us.kbase.kbasegenomes.Genome;
import us.kbase.workspace.GetObjectInfoNewParams;
import us.kbase.workspace.ObjectData;
import us.kbase.workspace.ObjectIdentity;
import us.kbase.workspace.WorkspaceClient;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.PrintWriter;
import java.math.RoundingMode;
import java.net.URL;
import java.text.DecimalFormat;
import java.text.NumberFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;


/**
 * Created by Marcin Joachimiak
 * User: marcin
 * Date: 12/17/14
 * Time: 9:41 PM
 */
public class GenometoGbk {


    boolean debug = true;
    //NC_009925.jsonp NC_009925_ContigSet.jsonp

    //object_name, object_id, object_version_number,
    String[] argsPossible = {"-ig", "--in_file_genome", "-ic", "--in_file_contig",
            "-o", "--output_file", "-on", "--object_name", "-oi", "--object_id",
            "-ov", "--object_version",
            "-w", "--workspace_name", "-wu", "--workspace_service_url", "-su", "--shock_service_url",
            "-wd", "--working_directory", "--test"};
    String[] argsPossibleMap = {"inputg", "inputg", "inputc", "inputc",
            "output", "output", "objectn", "objectn", "objecti", "objecti",
            "objectv", "objectv",
            "wsn", "wsn", "wsu", "wsu", "shocku", "shocku", "wd", "wd", "t"};


    boolean isTest = false;

    Genome genome;
    ContigSet contigSet;

    final static String molecule_type_short = "DNA";
    final static String molecule_type_long = "genome DNA";


    String wsurl;// = "http://blah.blah/";
    String wsname;
    static String shockurl;// = "https://kbase.us/services/shock-api/";

    String genomefile;
    String contigfile;
    String outfile;
    File workdir;

    String objectname;
    String objectid;
    Long objectversion;

    ObjectMapper mapper;

    boolean fromFile = false;

    WorkspaceClient wc;

    public GenometoGbk() {

    }

    public GenometoGbk(WorkspaceClient worksc) {
        wc = worksc;
    }

    /**
     * @param args
     * @throws Exception
     */
    public GenometoGbk(String[] args) throws Exception {


        init(args);


        run();
    }

    /**
     * @throws IOException
     * @throws AuthException
     * @throws JsonClientException
     */
    public void run() throws IOException, AuthException, JsonClientException {
        if (fromFile) {
            getDatafromFiles(mapper);
        } else {
            getDatafromWorkspace(mapper);
        }

        System.out.println(genome.getTaxonomy());

        List<Contig> contigs = contigSet.getContigs();

        StringBuffer out = createHeader(genome.getId(), 0, 0, "");
        for (int j = 0; j < contigs.size(); j++) {

            Contig curcontig = contigs.get(j);
            //if (j > 0)
            out = createHeader(curcontig.getId(), 1,curcontig.getLength(),curcontig.getName());

            out.append("ORIGIN\n");
            if (contigs.size() > 0) {

                out.append(formatDNASequence(curcontig.getSequence(), 10, 60));
                //out += "        1 tctcgcagag ttcttttttg tattaacaaa cccaaaaccc atagaattta atgaacccaa\n";//10
            }

            String numfile = "";
            if (contigs.size() > 0)
                numfile = "_" + j;
            String outname = "";
            if (outfile != null) {
                if (!outfile.endsWith(".gbk") && !outfile.endsWith(".gb") &&
                        !outfile.endsWith(".genbank") && !outfile.endsWith(".gbff") && !outfile.endsWith(".gbf")) {
                    outname = outfile + numfile + ".gbk";
                }
            } /*else if (curcontig.getName() != null && ) {
                outname = curcontig.getName() + ".gbk";
            }*/ else if (curcontig.getId() != null) {
                outname = curcontig.getId() + ".gbk";
            } else if (genome.getId() != null && curcontig.getId() != null) {
                outname = genome.getId() + "_" + curcontig.getId();
            }
            /*else if (objectname != null) {
                outname = objectname + numfile + ".gbk";
            } else if (objectid != null) {
                outname = objectid + numfile + ".gbk";
            } else if (genomefile != null) {
                int start = Math.max(0, genomefile.lastIndexOf("/"));
                int end = genomefile.lastIndexOf(".");
                outname = genomefile.substring(start, end) + numfile + ".gbk";
            }*/
            outname = outname.replace("|", "_");
            final String outpath = (workdir != null ? workdir + "/" : "") + outname;
            System.out.println("writing " + outpath);
            try {
                File outf = new File(outpath);
                PrintWriter pw = new PrintWriter(outf);
                pw.print(out);
                pw.close();
            } catch (FileNotFoundException e) {
                System.err.println("failed to write output " + outpath);
                e.printStackTrace();
            }
        }
    }

    /**
     *
     * @param contig_id
     * @param contigssize
     * @param contiglen
     * @param contig_name
     * @return
     */
    private StringBuffer createHeader(String contig_id, int contigssize, long contiglen, String contig_name) {
        StringBuffer out = new StringBuffer("");
        //out += "LOCUS       NC_005213             " + curcontig.getLength() + " bp    " + molecule_type_short + "     circular CON 10-JUN-2013\n";
        out.append("LOCUS       " + contig_id + "             " + contigssize + " bp    " +
                molecule_type_short + "\n");// + "     circular CON 10-JUN-2013\n");
        out.append("DEFINITION  " + genome.getScientificName() + " genome.\n");
        //out.append("ACCESSION   NC_005213\n");
        //out.append("VERSION     NC_005213.1  GI:38349555\n");
        //out += "DBLINK      Project: 58009\n";
        //out += "            BioProject: PRJNA58009\n";
        //out.append("KEYWORDS    .\n");
        out.append("SOURCE      " + genome.getScientificName() + "\n");
        out.append("  ORGANISM  " + genome.getScientificName() + "\n");
        final String rawTaxonomy = genome.getTaxonomy();

        String[] alltax = rawTaxonomy.split(" ");

        StringBuffer formatTax = new StringBuffer("");

        int counter = 0;
        int index = 0;
        while (index < alltax.length) {
            formatTax.append(alltax[index]);
            if (index < alltax.length - 1)
                formatTax.append(" ");
            counter += alltax[index].length() + 1;
            index++;
            if (counter >= 65 || rawTaxonomy.length() < 80) {
                formatTax.append("\n");
                formatTax.append("            ");
                counter = 0;
            }
        }

        out.append("            " + formatTax + ".\n");

            /*TODO populate references in Genome objects */
            /*
             //typedef tuple<int id, string source_db, string article_title, string link, string pubdate, string authors, string journal_name> publication;
            List<Tuple7<Long, String, String, String, String, String, String>> pubs = genome.getPublications();
            for (int k = 0; k < pubs.size(); k++) {
                Tuple7<Long, String, String, String, String, String, String> curpub = pubs.get(k);
                System.out.println(genome.getTaxonomy());
                System.out.println(curpub.getE6());
                out += "REFERENCE   1  (bases " + 1 + " to " + curcontig.getLength() + ")\n";
                out += "  AUTHORS   ";//Waters,E., Hohn,M.J., Ahel,I., Graham,D.E., Adams,M.D.,\n";
                for(int m=0;m<(curpub.getE6()).length();m++) {
                out+=
                //out += "            Barnstead,M., Beeson,K.Y., Bibbs,L., Bolanos,R., Keller,M.,\n";//59
                }
                out += "  TITLE     "+curpub.getE3()+"\n";//64
                out += "  JOURNAL   "+curpub.getE7()+"\n";
                //TODO Genome object missing JOURNAL volume issue pages etc.
                //+" 100 (22), 12984-12988 (2003)\n";
                if (curpub.getE2().equalsIgnoreCase("PUBMED"))
                    out += "   PUBMED   " + curpub.getE1() + "\n";
            }
        */

        //out += "COMMENT     PROVISIONAL REFSEQ: This record has not yet been subject to final\n";
        //out += "            NCBI review. The reference sequence was derived from AE017199.\n";
        out.append(" COMMENT            COMPLETENESS: " + (genome.getComplete() == 1 ? "full length" : "incomplete") + ".\n");
        out.append("                    Exported from the DOE KnowledgeBase.\n");


        out.append("FEATURES             Location/Qualifiers\n");
        out.append("     source          1.." + contiglen + "\n");
        out.append("                     /organism=\"" + genome.getScientificName() + "\"\n");
        out.append("                     /mol_type=\"" + molecule_type_long + "\"\n");
        //out += "                     /strain=\"\"\n";

        String taxId = null;
        Map<String, Object> addprops = genome.getAdditionalProperties();
        for (String k : addprops.keySet()) {
            //System.out.println("addprops " + k + "\t" + addprops.get(k));
            if (k.equals("tax_id"))
                taxId = "" + (Integer) addprops.get(k);

        }


        if (taxId != null)
            out.append("                     /db_xref=\"taxon:" + taxId + "\"\n");

        List<Feature> features = genome.getFeatures();


        for (int i = 0; i < features.size(); i++) {
            Feature cur = features.get(i);
            List<Tuple4<String, Long, String, Long>> location = cur.getLocation();

            //match features to their contig
            if (location.get(0).getE1().equals(contig_name) || location.get(0).getE1().equals(contig_id)) {
                //"location":[["kb|g.0.c.1",3378378,"+",1368]]
                //if (curcontig.getName().equals("NC_009926")) {
                    /*System.out.println("match feature to contig " + j + "\t" + location.get(0).getE1() + "\t" +
                            location.get(0).getE2() + "\t" + location.get(0).getE3() + "\t" + location.get(0).getE4() + "\t"
                            + curcontig.getName());*/
                String id = null;
                try {
                    final List<String> aliases = cur.getAliases();
                    if (aliases != null) {
                        try {
                            id = aliases.get(0);
                        } catch (Exception e) {
                            //e.printStackTrace();
                        }
                    }
                    if (id == null)
                        id = cur.getId();
                } catch (Exception e) {
                    e.printStackTrace();
                }

                String function = cur.getFunction();
                String[] allfunction = {""};
                if (function != null)
                    allfunction = function.split(" ");
                else
                    function = "";


                boolean test = false;

            /*if (id.equals("NP_963295.1")) {
                test = true;
                System.out.println("allfunction " + allfunction.length + "\t" + function.length());
            }*/

                StringBuffer formatNote = getAnnotation(function, allfunction, 51, 58, debug);
                StringBuffer formatFunction = getAnnotation(function, allfunction, 48, 58, debug);//51,58);

            /*TODO add operons and promoteres and terminators as gene features ? */
                if (id.indexOf(".opr.") == -1 && id.indexOf(".prm.") == -1 && id.indexOf(".trm.") == -1) {

                    if (cur.getType().equals("CDS")) //id.indexOf(".rna.") == -1)
                        out.append("     gene            ");
                    else {
                        if (function.indexOf("tRNA") != -1) {
                            out.append("     tRNA            ");
                        } else {
                            out.append("     misc_RNA        ");
                        }
                    }
                    out = getCDS(out, location);
                    out.append("                     /gene=\"" + id + "\"\n");
                    //out += "                     /db_xref=\"GeneID:2732620\"\n";
                    if (cur.getType().equals("CDS")) {
                        out.append("     CDS             ");
                        out = getCDS(out, location);
                        out.append("                     /gene=\"" + id + "\"\n");
                    }

                    out.append("                     /note=\"" + formatNote);
                    //out += "                     /codon_start=1\n";
                    //out += "                     /transl_table=11\n";
                    out.append("                     /product=\"" + id + "\"\n");
                    out.append("                     /function=\"" + formatFunction);

                    if (cur.getType().equals("CDS"))
                        out.append("                     /protein_id=\"" + id + "\"\n");

                    List<String> aliases = cur.getAliases();
                    if (aliases != null) {
                        for (String s : aliases) {
                            //System.out.println("adding alias " + s);
                            out.append("                     /db_xref=\"id:" + s + "\"\n");
                        }
                    }
                    //out += "                     /db_xref=\"GeneID:2732620\"\n";

                    //gene

                    final String proteinTranslation = cur.getProteinTranslation();
                    //System.out.println(proteinTranslation);
                    if (proteinTranslation != null)
                        out.append("                     /translation=\"" + formatString(proteinTranslation, 44, 58));
                    //else
                    //    System.out.println("op? " + id);
                }

                //if (test)
                //    System.exit(0);
                //}
            }
        }
        return out;
    }

    /**
     * @param args
     */
    public void init(String[] args) {
        for (int i = 0; i < args.length; i++) {
            int index = Arrays.asList(argsPossible).indexOf(args[i]);
            if (index > -1) {
                if (argsPossibleMap[index].equals("inputg")) {
                    genomefile = args[i + 1];
                } else if (argsPossibleMap[index].equals("inputc")) {
                    contigfile = args[i + 1];
                } else if (argsPossibleMap[index].equals("objectn")) {
                    objectname = args[i + 1];
                } else if (argsPossibleMap[index].equals("objecti")) {
                    objectid = args[i + 1];
                } else if (argsPossibleMap[index].equals("objectv")) {
                    objectversion = Long.getLong(args[i + 1]);
                } else if (argsPossibleMap[index].equals("output")) {
                    outfile = args[i + 1];
                } else if (argsPossibleMap[index].equals("wsn")) {
                    wsname = args[i + 1];
                } else if (argsPossibleMap[index].equals("wsu")) {
                    wsurl = args[i + 1];
                } else if (argsPossibleMap[index].equals("shocku")) {
                    shockurl = args[i + 1];
                } else if (argsPossibleMap[index].equals("wd")) {
                    workdir = new File(args[i + 1]);
                } else if (argsPossibleMap[index].equals("t")) {
                    if (args[i + 1].equalsIgnoreCase("Y") || args[i + 1].equalsIgnoreCase("yes") || args[i + 1].equalsIgnoreCase("T") || args[i + 1].equalsIgnoreCase("TRUE"))
                        isTest = true;
                }
            }
        }

        if (genomefile == null && contigfile == null) {
            if (objectname == null && objectid == null) {
                System.err.println("no object name or id provided and no input files provided");
            }
        }

        if (workdir == null) {
            workdir = new File("./");
            System.out.println("set work dir to default " + workdir);
        }
        if (!workdir.exists())
            workdir.mkdirs();

        mapper = UObject.getMapper();//new ObjectMapper();

        if (genomefile != null && contigfile != null) {
            fromFile = true;
        }
    }

    /**
     * @param mapper
     * @throws IOException
     */
    private void getDatafromFiles(ObjectMapper mapper) throws IOException {
        File loadGenome = new File(this.genomefile);
        File loadContigs = new File(this.contigfile);
        genome = mapper.readValue(loadGenome, Genome.class);
        contigSet = mapper.readValue(loadContigs, ContigSet.class);
    }


    /**
     * @param mapper
     * @throws AuthException
     * @throws IOException
     * @throws JsonClientException
     */
    private void getDatafromWorkspace(ObjectMapper mapper) throws AuthException, IOException, JsonClientException {

        String user = System.getProperty("test.user");
        String pwd = System.getProperty("test.pwd");

        String kbtok = System.getenv("KB_AUTH_TOKEN");

        if (wc == null) {
            System.out.println("new ws client");
            if (isTest) {
                AuthToken at = ((AuthUser) AuthService.login(user, pwd)).getToken();
                wc = new WorkspaceClient(new URL(wsurl + "/" + wsname), at);
            } else {
                wc = new WorkspaceClient(new URL(wsurl + "/" + wsname), new AuthToken(kbtok));
            }
            wc.setAuthAllowedForHttp(true);
        }

        List<ObjectIdentity> objectIds = new ArrayList<ObjectIdentity>();
        ObjectIdentity genobj = new ObjectIdentity();
        genobj.setName(objectname);
        String appendver = "";
        if (objectversion != null) {
            genobj.setVer(objectversion);
            appendver = "/" + objectversion;
        }
        genobj.setWorkspace(wsname);
        objectIds.add(genobj);

        System.out.println("getting Genome object " + wsname + "/" + objectname + appendver);
        long startg = System.currentTimeMillis();
        List<ObjectData> lod = wc.getObjects(objectIds);
        final UObject data1 = lod.get(0).getData();
        long endg = System.currentTimeMillis();

        final double doub = (double) (endg - startg) / (double) 1000;
        NumberFormat df = DecimalFormat.getInstance();
        df.setMinimumFractionDigits(2);
        df.setMaximumFractionDigits(2);
        df.setRoundingMode(RoundingMode.DOWN);
        String result = df.format(doub);
        System.out.println("got Genome in " + result + " s");

        genome = data1.asClassInstance(Genome.class);
        String contigref = genome.getContigsetRef();

        GetObjectInfoNewParams params = new GetObjectInfoNewParams();
        params.setObjects(objectIds);
        params.setIncludeMetadata(1L);

        List<Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>>> oinfo = wc.getObjectInfoNew(params);
        Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>> tup = oinfo.get(0);

        final double doub2 = (double) tup.getE10() / (double) (1024 * 1024);
        df = DecimalFormat.getInstance();
        df.setMinimumFractionDigits(2);
        df.setMaximumFractionDigits(2);
        df.setRoundingMode(RoundingMode.DOWN);
        String result2 = df.format(doub2);

        //DecimalFormat df = new DecimalFormat("0.00##");
        //String result = df.format(doub);

        System.out.println("got Genome object size " + result2 + "M");

        List<ObjectIdentity> objectIds2 = new ArrayList<ObjectIdentity>();
        ObjectIdentity contigobj = new ObjectIdentity();
        contigobj.setRef(contigref);
        objectIds2.add(contigobj);
        System.out.println("got contigref " + contigref);
        try {

            long startg2 = System.currentTimeMillis();
            List<ObjectData> lod2 = wc.getObjects(objectIds2);
            long endg2 = System.currentTimeMillis();
            final UObject data2 = lod2.get(0).getData();
            final double doub3 = (double) (endg2 - startg2) / (double) 1000;
            df = DecimalFormat.getInstance();
            df.setMinimumFractionDigits(2);
            df.setMaximumFractionDigits(2);
            df.setRoundingMode(RoundingMode.DOWN);
            String result3 = df.format(doub3);

            System.out.println("got ContigSet in " + result3 + " s");

            contigSet = data2.asClassInstance(ContigSet.class);

            GetObjectInfoNewParams params2 = new GetObjectInfoNewParams();
            params2.setObjects(objectIds2);
            params2.setIncludeMetadata(1L);
            //System.out.println(Instrumentation.getObjectSize(contigSet));
            List<Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>>> oinfo2 = wc.getObjectInfoNew(params2);
            Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>> tup2 = oinfo2.get(0);

            final double doub4 = (double) tup2.getE10() / (double) (1024 * 1024);
            df = DecimalFormat.getInstance();
            df.setMinimumFractionDigits(2);
            df.setMaximumFractionDigits(2);
            df.setRoundingMode(RoundingMode.DOWN);
            String result4 = df.format(doub4);

            System.out.println("got ContigSet object number " + contigSet.getContigs().size() + ", size " + result4 + "M");
        } catch (Exception e) {
            System.err.println("ContigSet not found in workspace.");

            /*String outputfile = args[0] + "_ContigSet.json";
            try {
                BasicShockClient client = null;
                if (isTest) {
                    AuthToken at = ((AuthUser) AuthService.login(user, pwd)).getToken();
                    client = new BasicShockClient(new URL(shockurl), at);
                } else {
                    client = new BasicShockClient(new URL(shockurl), new AuthToken(kbtok));
                }
                OutputStream os = new FileOutputStream(new File(outputfile));

                client.getFile(new ShockNodeId(contigref), os);

                os.close();
            } catch (InvalidShockUrlException e1) {
                System.err.println("Invalid Shock url.");
                e1.printStackTrace();
            } catch (ShockHttpException e1) {
                System.err.println("Shock HTPP error.");
                e1.printStackTrace();
            }
            File loadContigs = new File(args[1]);
            contigSet = mapper.readValue(loadContigs, ContigSet.class);
            */
        }

    }

    /**
     * @param function
     * @param allfunction
     * @return
     */
    private StringBuffer getAnnotation(String function, String[] allfunction, int first, int next, boolean debug) {
        //if (debug)
        //    System.out.println("getAnnotation " + first + "\t" + next);
        StringBuffer formatFunction = new StringBuffer("");
        //73
        boolean isfirst = true;
        if (function.length() < first) {
            formatFunction.append(function + "\"\n");
        } else {
            int counter2 = 0;
            int index2 = 0;
            while (index2 < allfunction.length) {
                //if (debug) {
                //System.out.println("allfunction index2 " + index2 + "\t" + allfunction[index2]);
                //    System.out.println("allfunction counter2 1 " + counter2);
                //}

                counter2 += allfunction[index2].length() + 1;
                /*if (debug) {
                    StringBuffer debugStr = new StringBuffer("");
                    debugStr.append("index2 " + index2 + "\t");
                    debugStr.append("counter2 " + counter2 + "\t");
                    debugStr.append("index2 + 1 " +
                            (index2 + 1 < allfunction.length ? (counter2 + allfunction[index2 + 1].length()) : "NaN") + "\t");
                    debugStr.append("allfunction[index2].length() " + allfunction[index2].length() + "\t");
                    debugStr.append("index2 + 1 < allfunction.length " +
                            (index2 + 1 < allfunction.length ? allfunction[index2 + 1].length() : "NaN") + "\t");
                    debugStr.append("allfunction[index2] " + allfunction[index2] + "\t");
                    debugStr.append("index2 + 1 " + (index2 + 1 < allfunction.length ? allfunction[index2 + 1] : "NaN") + "\t");
                    System.out.println("allfunction end " + debugStr);
                }*/


                if (((isfirst && counter2 >= first) || counter2 >= next)) {
                    // if (debug)
                    //    System.out.println("new line");
                    if (isfirst)
                        isfirst = false;

                    if (index2 < allfunction.length) {
                        formatFunction.append("\n");
                        formatFunction.append("                     ");
                        formatFunction.append(allfunction[index2]);
                        counter2 = allfunction[index2].length();
                        if (index2 < allfunction.length - 1) {
                            counter2++;
                            formatFunction.append(" ");
                        } else
                            formatFunction.append("\"\n");
                    }
                } else {
                    if (index2 < allfunction.length) {
                        formatFunction.append(allfunction[index2]);
                        if (index2 < allfunction.length - 1) {
                            counter2++;
                            formatFunction.append(" ");
                        } else
                            formatFunction.append("\"\n");
                    } else
                        formatFunction.append("\"\n");
                }

                index2++;
            }
        }
        if (formatFunction.length() == 0) {
            formatFunction.append("\"\n");
        }
        return formatFunction;
    }

    /**
     * @param out
     * @param location
     * @return
     */
    private StringBuffer getCDS(StringBuffer out, List<Tuple4<String, Long, String, Long>> location) {
        int added = 0;
        boolean complement = false;
        boolean join = false;
        for (int n = 0; n < location.size(); n++) {
            Tuple4<String, Long, String, Long> now4 = location.get(n);
            //System.out.println("getCDS " + now4);
            if (added == 0 && now4.getE3().equals("-")) {
                out.append("complement(");
                complement = true;
            }
            //System.out.println("complement " + complement + "\t" + now4.getE3());
            if (location.size() > 1) {
                if (added == 0)
                    out.append("join(");
                join = true;
            }

            if (!complement) {
                //System.out.println("location +");
                out.append(now4.getE2() + ".." + (now4.getE2() + (long) now4.getE4() - 1));
            } else {
                //System.out.println("location -");
                out.append((now4.getE2() - (long) now4.getE4() + 1) + ".." + now4.getE2());
            }

            if (location.size() > 0 && n < location.size() - 1)
                out.append(",");
            added++;

            //complement = false;
        }
        if (complement && join)
            out.append("))\n");
        else if (complement || join) {
            out.append(")\n");
        } else
            out.append("\n");


        return out;
    }


    /**
     * @param s
     * @param one
     * @param two
     * @return
     */
    public StringBuffer formatString(String s, int one, int two) {
        //StringBuilder out = new StringBuilder("");
        StringBuffer out = new StringBuffer("");
        boolean first = true;
        for (int start = 0; start < s.length(); ) {
            if (first) {
                int last = Math.min(s.length(), start + one);
                boolean isLast = false;
                if (last == s.length())
                    isLast = true;
                out.append(s.substring(start, last));
                if (isLast)
                    out.append("\"\n");
                else {
                    out.append("\n");
                }
                first = false;
                start += one;
            } else {
                int last = Math.min(s.length(), start + two);
                //System.out.println(s.length() + "\t" + (start + two));
                out.append("                     ");
                boolean isLast = false;
                if (last == s.length())
                    isLast = true;
                out.append(s.substring(start, last));
                start += two;
                if (isLast) {
                    //out.append(s.substring(start, s.length()-1));
                    out.append("\"\n");
                }
                //} else if (start < s.length()) {
                else
                    out.append("\n");
                //} //else if (start < s.length()) {
                //    out.append("\n");
                //} //else
                //  out.append("\n");
            }
        }

        return out;
    }

    /**
     * @param s
     * @param charnum
     * @param linenum
     * @return
     */
    public StringBuffer formatDNASequence(String s, int charnum, int linenum) {
        //StringBuilder out = new StringBuilder("");
        StringBuffer out = new StringBuffer("");

        //out += "        1 tctcgcagag ttcttttttg tattaacaaa cccaaaaccc atagaattta atgaacccaa\n";//10

        out.append("        1 ");
        int index = 1;
        int counter = 0;
        for (int last = 0; last < s.length(); ) {
            int end = Math.min(s.length(), last + charnum);
            //if (end > s.length())
            //   end = s.length();
            //System.out.println("DNA " + last + "\t" + end);
            out.append(s.substring(last, end));
            last += charnum;
            counter++;
            if (counter == 6 && s.length() > end) {
                out.append("\n");
                index += 60;
                String indexStr = "" + index;
                int len = indexStr.length();
                char[] ch = new char[9 - len];
                Arrays.fill(ch, ' ');
                String padStr = new String(ch);
                out.append(padStr + indexStr + " ");
                counter = 0;
            } else
                out.append(" ");
        }
        if (out.charAt(out.length() - 1) == (' '))
            out.deleteCharAt(out.length() - 1);

        return out;
    }


    /**
     * @param args
     */
    public final static void main(String[] args) {
        //System.out.println(args.length % 2);

        if (args.length % 2 == 0 && args.length > 1) {
            try {
                GenometoGbk gtg = new GenometoGbk(args);
            } catch (Exception e) {
                e.printStackTrace();
            }
        } else {
            System.out.println("usage: java us.kbase.genbank.GenometoGbk " +

                    "<-ig or --in_file_genome Genome object json file> " +
                    "<-ic or --in_file_contig ContigSet object json file> " +
                    "<-o or --output_file> " +
                    "<-on or --object_name> " +
                    "<-oi or --object_id> " +
                    "<-ov or --object_version> " +
                    "<-w or --workspace_name ws name> " +
                    "<-wu or --workspace_service_url ws url> " +
                    "<-su or --shock_service_url shock url> " +
                    "<-wd or --working_directory");


           /* String[] argsPossible = {"-ig", "--in_file_genome","-ic","--in_file_contig",
                    "-o", "--out_file", "-on","--object_name","-oi","--object_id",
                   "-ov","--object_version",
                    "-w", "--workspace_name", "-wu", "--workspace_url", "-su", "--shock_url", "-wd", "--working_directory"};*/

            //"<Genome .json (XXXX.json) or Genome object name in workspace> " +
            // "<ContigSet .json (XXXX_ContigSet.json) or ContigSet object name in workspace> " +
            //"<OTPIONAL workspace name (and then REQUIRED Genome object name and ContigSet name>");
        }
    }

}


 /*
LOCUS       NC_005213             490885 bp    DNA     circular CON 10-JUN-2013
 DEFINITION  Nanoarchaeum equitans Kin4-M chromosome, complete genome.
 ACCESSION   NC_005213
 VERSION     NC_005213.1  GI:38349555
 DBLINK      Project: 58009
             BioProject: PRJNA58009
 KEYWORDS    .
 SOURCE      Nanoarchaeum equitans Kin4-M
   ORGANISM  Nanoarchaeum equitans Kin4-M
             Archaea; Nanoarchaeota; Nanoarchaeum.
 REFERENCE   1  (bases 1 to 490885)
   AUTHORS   Waters,E., Hohn,M.J., Ahel,I., Graham,D.E., Adams,M.D.,
             Barnstead,M., Beeson,K.Y., Bibbs,L., Bolanos,R., Keller,M.,
             Kretz,K., Lin,X., Mathur,E., Ni,J., Podar,M., Richardson,T.,
             Sutton,G.G., Simon,M., Soll,D., Stetter,K.O., Short,J.M. and
             Noordewier,M.
   TITLE     The genome of Nanoarchaeum equitans: insights into early archaeal
             evolution and derived parasitism
   JOURNAL   Proc. Natl. Acad. Sci. U.S.A. 100 (22), 12984-12988 (2003)
    PUBMED   14566062
 REFERENCE   2  (bases 1 to 490885)
   CONSRTM   NCBI Genome Project
   TITLE     Direct Submission
   JOURNAL   Submitted (17-NOV-2003) National Center for Biotechnology
             Information, NIH, Bethesda, MD 20894, USA
 REFERENCE   3  (bases 1 to 490885)
   CONSRTM   NCBI Microbial Genomes Annotation Project
   TITLE     Direct Submission
   JOURNAL   Submitted (25-JUN-2001) National Center for Biotechnology
             Information, NIH, Bethesda, MD 20894, USA
 COMMENT     PROVISIONAL REFSEQ: This record has not yet been subject to final
             NCBI review. The reference sequence was derived from AE017199.
             COMPLETENESS: full length.
 FEATURES             Location/Qualifiers
      source          1..490885
                      /organism="Nanoarchaeum equitans Kin4-M"
                      /mol_type="genomic DNA"
                      /strain="Kin4-M"
                      /db_xref="taxon:228908"
 gene            complement(486423..486962)
                 /locus_tag="NEQ550"
                 /db_xref="GeneID:2732580"
 CDS             complement(486423..486962)
                 /locus_tag="NEQ550"
                 /codon_start=1
                 /transl_table=11
                 /product="hypothetical protein"
                 /protein_id="NP_963830.1"
                 /db_xref="GI:41615332"
                 /db_xref="GeneID:2732580"
                 /translation="MLELLAGFKQSILYVLAQFKKPEYATSYTIKLVNPFYYISDSLN
                 VITSTKEDKVNYKVSLSDIAFDFPFKFPIVAIVEGKANREFTFIIDRQNKKLSYDLKK
                 GIIYIQDATIIPNGIKITVNGLAELKNIKINPNDPSITVQKVVGEQNTYIIKTSKDSV
                 KITISADFVVKAEKWLFIQ"
 promoter        486983..486988
                 /note="archaeal RNA pol III promoter consensus box Aaaaaaa
                 motif"
 misc_feature    487009..487022
                 /locus_tag="NEQ_t33"
                 /note="reverse complementary sequence cleaved during
                 processing of trans-spliced tRNAs"
ORIGIN
    1 tctcgcagag ttcttttttg tattaacaaa cccaaaaccc atagaattta atgaacccaa
   61 accgcaatcg tacaaaaatt tgtaaaattc tctttcttct ttgtctaatt ttctataaac
  121 atttaactct ttccataatg tgcctatata tactgcttcc cctctgttaa ttcttattct
  */