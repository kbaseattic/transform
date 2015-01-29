package us.kbase.genbank;

import us.kbase.auth.AuthService;
import us.kbase.auth.AuthToken;
import us.kbase.auth.AuthUser;
import us.kbase.auth.TokenFormatException;
import us.kbase.common.service.JsonClientException;
import us.kbase.common.service.Tuple11;
import us.kbase.common.service.UObject;
import us.kbase.common.service.UnauthorizedException;
import us.kbase.kbasegenomes.Contig;
import us.kbase.kbasegenomes.ContigSet;
import us.kbase.kbasegenomes.Genome;
import us.kbase.workspace.*;

import java.io.*;
import java.math.BigInteger;
import java.net.URL;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;

/*
import us.kbase.shock.client.BasicShockClient;
import us.kbase.shock.client.ShockNode;
import us.kbase.shock.client.exceptions.InvalidShockUrlException;
import us.kbase.shock.client.exceptions.ShockHttpException;
*/

/**
 * Created by Marcin Joachimiak
 * User: marcin
 * Date: 11/3/14
 * Time: 3:22 PM
 */
public class ConvertGBK {

    //--workspace_service_url {0}--workspace_name {1} --object_name {2} --contigset_object_name {3} "
    String[] argsPossible = {"-i", "--input_directory", "-o", "--object_name", "-oc", "--contigset_object_name",
            "-w", "--workspace_name", "-wu", "--workspace_service_url", "-su", "--shock_url", "-wd", "--working_directory", "--test"};
    String[] argsPossibleMap = {"input", "input", "outputg", "outputg", "outputc", "outputc",
            "wsn", "wsn", "wsu", "wsu", "shocku", "shocku", "wd", "wd", "t"};

    static String wsurl = null;
    static String shockurl = null;

    String wsname = null;

    String workdir;

    String out_object_g = null;
    String out_object_c = null;
    File indir;

    String allowed_objname_chars = "|._-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";


    boolean isTest = false;

    /**
     * @param args
     * @throws Exception
     */
    public ConvertGBK(String[] args) throws Exception {

        for (int i = 0; i < args.length; i++) {
            int index = Arrays.asList(argsPossible).indexOf(args[i]);
            if (index > -1) {
                if (argsPossibleMap[index].equals("input")) {
                    indir = new File(args[i + 1]);
                } else if (argsPossibleMap[index].equals("outputg")) {
                    out_object_g = args[i + 1];
                } else if (argsPossibleMap[index].equals("outputc")) {
                    out_object_c = args[i + 1];
                } else if (argsPossibleMap[index].equals("wsn")) {
                    wsname = args[i + 1];
                } else if (argsPossibleMap[index].equals("wsu")) {
                    wsurl = args[i + 1];
                } else if (argsPossibleMap[index].equals("shocku")) {
                    shockurl = args[i + 1];
                } else if (argsPossibleMap[index].equals("wd")) {
                    workdir = args[i + 1];
                } else if (argsPossibleMap[index].equals("t")) {
                    if (args[i + 1].equalsIgnoreCase("Y") || args[i + 1].equalsIgnoreCase("yes") || args[i + 1].equalsIgnoreCase("T") || args[i + 1].equalsIgnoreCase("TRUE"))
                        isTest = true;
                }
            }
        }

        System.out.println("indir " + indir);
        System.out.println("wsname " + wsname);
        System.out.println("wsurl " + wsurl);
        System.out.println("isTest " + isTest);

        if (workdir == null) {
            File tmpf = new File("./");
            workdir = tmpf.getAbsolutePath();
        }

        if (workdir.endsWith("/.")) {
            workdir = workdir.substring(0, workdir.length() - 2);
        }


        int start = "LOCUS       ".length();
        if (indir.isDirectory()) {
            final String splitpath = indir.getAbsolutePath() + "/split";
            File[] files = indir.listFiles(new FilenameFilter() {
                @Override
                public boolean accept(File dir, String name) {
                    return name.matches("^.*\\.(gb|gbk|genbank|gbf|gbff)$");
                }
            });
            for (int i = 0; i < files.length; i++) {
                boolean wasSplit = splitRecord(start, files[i], splitpath);
                if (wasSplit && files.length > 1) {
                    System.err.println("Multiple multi-record Genbank files currently not supported.");
                } else if (wasSplit) {
                    System.out.println("Split single input file " + files[i].getName() + " into muultiple records? " + wasSplit);
                    indir = new File(indir.getAbsolutePath() + "/split");
                }
            }
        } else {
            boolean wasSplit = splitRecord(start, indir, null);
            System.out.println("Split single input file into muultiple records? " + wasSplit);
            if (wasSplit) {
                indir = new File("./split");
            }
        }


        parseAllInDir(new int[]{1}, indir, new ObjectStorage() {
            @Override
            public List<Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>>> saveObjects(
                    String authToken, SaveObjectsParams params) throws Exception {
                //validateObject(validator, params.getObjects().get(0).getName(),
                //			params.getObjects().get(0).getData(), params.getObjects().get(0).getType());
                return null;
            }

            @Override
            public List<ObjectData> getObjects(String authToken,
                                               List<ObjectIdentity> objectIds) throws Exception {
                throw new IllegalStateException("Unsupported method");
            }
        }, wsname, wsurl, isTest);
    }

    /**
     * @param start
     * @throws FileNotFoundException
     */
    private boolean splitRecord(int start, File path, String outpath) throws FileNotFoundException {

        boolean split = false;
        Scanner fileScanner = new Scanner(path);
        List<String> locitest = new ArrayList<String>();
        while (fileScanner.hasNextInt()) {
            String cur = fileScanner.next();
            if (cur.indexOf("LOCUS") == 0) {
                String curlocus = cur.substring(start, cur.indexOf(" ", start + 1));
                locitest.add(curlocus);
                if (locitest.size() > 1) {
                    break;
                }
            }
        }

        if (locitest.size() > 1) {

            if (outpath == null)
                outpath = "./split";

            File splitdir = new File(outpath);
            if (!splitdir.exists()) {
                splitdir.mkdir();
            }

            fileScanner = new Scanner(indir);
            List<String> loci = new ArrayList<String>();
            StringBuilder sb = new StringBuilder("");
            while (fileScanner.hasNextInt()) {
                String cur = fileScanner.next();
                if (cur.indexOf("LOCUS") == 0) {
                    String curlocus = cur.substring(start, cur.indexOf(" ", start + 1));
                    loci.add(curlocus);
                    sb.append(cur);
                } else if (cur.indexOf("//") != -1) {
                    String curoutpath = outpath + "/" + loci.get(loci.size() - 1) + ".gbk";
                    try {
                        PrintWriter out = new PrintWriter(new FileWriter(curoutpath));
                        out.print(sb);
                        out.close();
                        split = true;
                        System.out.println("    wrote: " + outpath);
                    } catch (IOException e) {
                        System.err.println("Error creating or writing file " + outpath);
                        System.err.println("IOException: " + e.getMessage());
                    }

                    sb = new StringBuilder("");
                }
            }
        }
        return split;
    }


    /**
     * @param pos
     * @param dir
     * @param wc
     * @throws Exception
     */
    public void parseAllInDir(int[] pos, File dir, ObjectStorage wc, String wsname, String http, boolean isTestThis) throws Exception {
        List<File> files = new ArrayList<File>();

        if (dir.isDirectory()) {
            for (File f : dir.listFiles()) {
                if (f.isDirectory()) {
                    parseAllInDir(pos, f, wc, wsname, http, isTestThis);
                } else if (f.getName().matches("^.*\\.(gb|gbk|genbank|gbf|gbff)$")) {
                    files.add(f);
                    System.out.println("Added " + f);
                }
            }
        } else {
            files.add(dir);
        }
        if (files.size() > 0)
            parseGenome(pos, dir, files, wsname, http, isTestThis);

    }

    /**
     * @param pos
     * @param dir
     * @param gbkFiles
     * @throws Exception
     */
    public void parseGenome(int[] pos, File dir, List<File> gbkFiles, String wsname, String http, boolean isTestThis) throws Exception {
        System.out.println("[" + (pos[0]++) + "] " + dir.getName());
        long time = System.currentTimeMillis();
        //System.out.println("parseGenome "+wsname);
        ArrayList ar = GbkUploader.uploadGbk(gbkFiles, wsname, dir.getName(), true);

        Genome genome = (Genome) ar.get(2);

      /*  List<Feature> features = genome.getFeatures();
        for (int i = 0; i < features.size(); i++) {
            Feature cur = features.get(i);
            System.out.println("parseGenome "+i + "\t" + cur.getAliases());
        }*/

        genome.setAdditionalProperties("SOURCE", "KBASE_USER_UPLOAD");
        String outpath = workdir + "/" + out_object_g + ".jsonp";

        System.out.println("workdir " + workdir + "\tout_object_g " + out_object_g + "\tout_object_c " + out_object_c);
        if (out_object_g == null) {
            out_object_g = genome.getId();
            outpath = workdir + "/" + out_object_g + ".jsonp";
        }
        try {
            PrintWriter out = new PrintWriter(new FileWriter(outpath));
            out.print(UObject.transformObjectToString(genome));
            out.close();
            System.out.println("    wrote: " + outpath);
        } catch (IOException e) {
            System.err.println("Error creating or writing file " + outpath);
            System.err.println("IOException: " + e.getMessage());
        }

        ContigSet contigSet = (ContigSet) ar.get(4);
        //final String contigId = genome.getId() + "_ContigSet";

        String outpath2 = workdir + "/" + out_object_c;//contigId + ".jsonp";
        if (out_object_c == null) {
            if (out_object_g != null) {
                //int start = 0;
                //if (out_object_g.lastIndexOf("/") != -1) {
                //     start = out_object_g.lastIndexOf("/");
                //}
                //final int endIndex = out_object_g.lastIndexOf(".");
                out_object_c = out_object_g + "__ContigSet";//out_object_g.substring(start, endIndex != -1 ? endIndex : out_object_g.length());
            } else {
                out_object_c = genome.getId() + "_ContigSet";
            }
        }

        if (out_object_c.indexOf("ContigSet") == -1)
            outpath2 = workdir + "/" + out_object_c + "_ContigSet.jsonp";
        else if (!out_object_c.endsWith(".json") && !out_object_c.endsWith(".jsonp"))
            outpath2 = workdir + "/" + out_object_c + ".jsonp";
        else
            outpath2 = workdir + "/" + out_object_c;

        try {
            PrintWriter out = new PrintWriter(new FileWriter(outpath2));
            out.print(UObject.transformObjectToString(contigSet));
            out.close();
            System.out.println("    wrote: " + outpath2);
        } catch (IOException e) {
            System.err.println("Error creating or writing file " + outpath2);
            System.err.println("IOException: " + e.getMessage());
        }

        List<Contig> contigs = contigSet.getContigs();
        ArrayList md5s = new ArrayList();
        for (int j = 0; j < contigs.size(); j++) {
            Contig curcontig = contigs.get(j);
            final String md5 = MD5(curcontig.getSequence().toUpperCase());
            md5s.add(md5);
            curcontig.setMd5(md5);
            contigs.set(j, curcontig);
        }
        contigSet.setContigs(contigs);


        Collections.sort(md5s);
        StringBuilder out = new StringBuilder();
        for (Object o : md5s) {
            out.append(o.toString());
            out.append(",");
        }
        out.deleteCharAt(out.length() - 1);

        String globalmd5 = out.toString();

        genome.setMd5(MD5(globalmd5));

        if (wsname != null) {

            /*ar.add(ws);
            ar.add(id);
            ar.add(genome);
            ar.add(contigSetId);
            ar.add(contigSet);
            ar.add(meta);*/

            //String genomeid = (String) ar.get(1);
            //String token = (String) ar.get(2);

            String contigSetId = (String) ar.get(3);

            Map<String, String> meta = (Map<String, String>) ar.get(5);

            String user = System.getProperty("test.user");
            String pwd = System.getProperty("test.pwd");

            String kbtok = System.getenv("KB_AUTH_TOKEN");

            //System.out.println(http);

            try {
                WorkspaceClient wc = null;

                if (isTestThis) {
                    System.out.println("using test mode");
                    AuthToken at = ((AuthUser) AuthService.login(user, pwd)).getToken();
                    wc = new WorkspaceClient(new URL(http), at);
                } else {
                    wc = new WorkspaceClient(new URL(http), new AuthToken(kbtok));
                }

                wc.setAuthAllowedForHttp(true);
                String gname = contigSetId;
                if (out_object_g != null) {
                    gname = out_object_g;
                }
                gname = sanitizeObjectName(gname);
                System.out.println("saving Genome " + gname);
                wc.saveObjects(new SaveObjectsParams().withWorkspace(wsname)
                        .withObjects(Arrays.asList(new ObjectSaveData().withName(gname).withMeta(meta)
                                .withType("KBaseGenomes.Genome").withData(new UObject(genome)))));
                System.out.println("successfully saved object");

                /*TODO create provenance string --- uploaded by transform service, user*/
                try {
                    String cname = contigSetId;
                    if (out_object_c != null) {
                        cname = out_object_c;
                    }
                    cname = sanitizeObjectName(cname);
                    System.out.println("saving ContigSet " + cname);
                    wc.saveObjects(new SaveObjectsParams().withWorkspace(wsname)
                            .withObjects(Arrays.asList(new ObjectSaveData().withName(cname)
                                    .withType("KBaseGenomes.ContigSet").withData(new UObject(contigSet)))));
                    System.out.println("successfully saved object");
                /*TODO add shock reference*/
                    //genome.setContigsetRef(contignode.getId().getId());
                } catch (IOException e) {
                    System.err.println("Error saving ContigSet to workspace, data may be too large (IOException)).");
                    e.printStackTrace();
                } catch (JsonClientException e) {
                    System.err.println("Error saving ContigSet to workspace, data may be too large (JsonClientException).");
                    e.printStackTrace();
                }

/*
                try {
                    BasicShockClient client = null;
                    if (isTestThis) {
                        AuthToken at = ((AuthUser) AuthService.login(user, pwd)).getToken();
                        client = new BasicShockClient(new URL(shockurl), at);
                    } else {
                        client = new BasicShockClient(new URL(shockurl), new AuthToken(kbtok));
                    }

                    InputStream os = new FileInputStream(new File(outpath2));
                    //upload ContigSet
                    ShockNode contignode = client.addNode(os, outpath2, "JSON");

                    genome.setContigsetRef(contignode.getId().getId());

                    //upload input GenBank files
                    for (File f : gbkFiles) {
                        os = new FileInputStream(f);
                        ShockNode sn = client.addNode(os, f.getName(), "TXT");
                        //genome.setFastaRef(sn.getId().getId());
                    }

                    os.close();
                } catch (InvalidShockUrlException e) {
                    System.err.println("Invalid Shock url.");
                    e.printStackTrace();
                } catch (ShockHttpException e) {
                    System.err.println("Shock HTPP error.");
                    e.printStackTrace();
                }
*/
            } catch (UnauthorizedException e) {
                System.err.println("WS UnauthorizedException");
                System.err.print(e.getMessage());
                System.err.print(e.getStackTrace());
                e.printStackTrace();
            } catch (IOException e) {
                System.err.println("WS IOException");
                System.err.print(e.getMessage());
                System.err.print(e.getStackTrace());
                e.printStackTrace();
            } catch (TokenFormatException e) {
                System.err.println("WS TokenFormatException");
                System.err.print(e.getMessage());
                System.err.print(e.getStackTrace());
                e.printStackTrace();
            }
        }

        System.out.println("    time: " + (double) (System.currentTimeMillis() - time) / (double) 1000 + " s");
    }

    /**
     * @param s
     * @return
     */
    public String sanitizeObjectName(String s) {
        StringBuilder sb = new StringBuilder(s);
        for (int i = 0; i < s.length(); i++) {
            if (allowed_objname_chars.indexOf(s.charAt(i)) == -1) {
                sb.setCharAt(i, '_');
            }
        }
        return sb.toString();
    }

    /**
     * @param s
     * @return
     */

    public static String MD5(String s) throws NoSuchAlgorithmException {
        MessageDigest m = MessageDigest.getInstance("MD5");
        m.update(s.getBytes(), 0, s.length());
        final String s1 = new BigInteger(1, m.digest()).toString(16);
        System.out.println("MD5: " + s1);
        return s1;
    }


    /**
     * @param args
     */
    public final static void main(String[] args) {
        if (args.length == 2 || args.length == 4 || args.length == 6 || args.length == 8 || args.length == 10 || args.length == 12 || args.length == 14) {
            try {
                ConvertGBK clt = new ConvertGBK(args);
            } catch (Exception e) {
                e.printStackTrace();
            }
        } else {
            /*TODO add ws url, output Genome object name, output ContigSet object name to arguments*/
            System.out.println("usage: java us.kbase.genbank.ConvertGBK " +
                    "<-i or --input_directory file or dir or files of GenBank .gbk files> " +
                    "<-o or --object_name> " +
                    "<-oc or --contigset_object_name> " +
                    "<-w or --workspace_name ws name> " +// <convert y/n> <save y/n>");
                    "<-wu or --workspace_service_url ws url> " +// <convert y/n> <save y/n>");
                    "<-su or --shock_url shock url> " +
                    "<-wd or --working_directory> " +
                    "<--test>");// <convert y/n> <save y/n>");

            //--workspace_service_url {0}--workspace_name {1} --object_name {2} --contigset_object_name {3} "
        }
    }

}
