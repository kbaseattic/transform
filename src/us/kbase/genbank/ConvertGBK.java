package us.kbase.genbank;

import us.kbase.auth.AuthService;
import us.kbase.auth.AuthToken;
import us.kbase.auth.AuthUser;
import us.kbase.auth.TokenFormatException;
import us.kbase.common.service.ServerException;
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
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
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
            "-w", "--workspace_name", "-wu", "--workspace_service_url", "-su", "--shock_url", "-wd", "--working_directory",
            "--test"};
    String[] argsPossibleMap = {"input", "input", "outputg", "outputg", "outputc", "outputc",
            "wsn", "wsn", "wsu", "wsu", "shocku", "shocku", "wd", "wd", "t"};

    static String wsurl = null;
    static String shockurl = null;

    String wsname = null;

    File workdir;
    String out_object_g = null;
    String out_object_c = null;
    File indir;
    File splitdir;

    String allowed_objname_chars = "|._-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

    WorkspaceClient wc = null;

    int MAX_ALLOWED_FILES = 10000;

    boolean isTest = false;


    /**
     * @param workc
     * @throws Exception
     */
    public ConvertGBK(WorkspaceClient workc) throws Exception {
        wc = workc;
    }

    /**
     * @param args
     * @throws Exception
     */
    public ConvertGBK(String[] args) throws Exception {

        init(args);

        run();

        System.out.println("finished");
    }

    /**
     * @throws Exception
     */
    public void run() throws Exception {
        System.out.println("indir " + indir);

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
     * @param args
     * @throws FileNotFoundException
     */
    public void init(String[] args) throws FileNotFoundException {
        for (int i = 0; i < args.length; i++) {
            int index = Arrays.asList(argsPossible).indexOf(args[i]);
            if (index > -1) {
                if (argsPossibleMap[index].equals("input")) {
                    String arg = args[i + 1];
                    if (arg.startsWith("./"))
                        arg = arg.substring(2);
                    indir = new File(arg);
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
                    workdir = new File(args[i + 1]);
                } else if (argsPossibleMap[index].equals("t")) {
                    if (args[i + 1].equalsIgnoreCase("Y") || args[i + 1].equalsIgnoreCase("yes") ||
                            args[i + 1].equalsIgnoreCase("T") || args[i + 1].equalsIgnoreCase("TRUE"))
                        isTest = true;
                }
            }
        }

        System.out.println("indir " + indir);
        System.out.println("wsname " + wsname);
        System.out.println("wsurl " + wsurl);
        System.out.println("isTest " + isTest);

        if (workdir == null) {
            workdir = new File(Paths.get(".").toAbsolutePath().normalize().toString());
        }
        if (!workdir.exists()) {
            workdir.mkdirs();
        }

        System.out.println("workdir 1 " + workdir.getAbsolutePath());

        int start = "LOCUS       ".length();

        System.out.println("input " + indir);

        if (indir.isDirectory()) {
            File[] files = indir.listFiles(new FilenameFilter() {
                @Override
                public boolean accept(File dir, String name) {
                    return name.matches("^.*\\.(gb|gbk|genbank|gbf|gbff)$");
                }
            });
            System.out.println("testing name matches " + files.length + "\t" + files[0]);

            String outpath = workdir.getAbsolutePath();

            int maxfiles = Math.min(files.length, MAX_ALLOWED_FILES);
            if (maxfiles < files.length) {
                final String outpath2 = (workdir != null ? workdir + "/" : "") + "README.txt";
                System.out.println("writing " + outpath2);
                try {
                    File outf = new File(outpath2);
                    PrintWriter pw = new PrintWriter(outf);

                    String readmestr = "The limit for uploading is " + MAX_ALLOWED_FILES + " files. This download had " + files.length
                            + " files, however only the first " + MAX_ALLOWED_FILES + " will be uploaded.";
                    pw.print(readmestr);
                    pw.close();
                } catch (FileNotFoundException e) {
                    System.err.println("failed to write output " + outpath);
                    e.printStackTrace();
                }
            }


            long size = 0;
            for (int i = 0; i < maxfiles; i++) {
                size += Math.abs(files[i].length());
            }
            final long max = Math.abs(2 * 1024 * 1024 * 1024);
            if (size > Math.abs(max)) {
                final String x = "Inputs are too large " + (size / (double) (1024 * 1024) + "G. Max allowed size is 2G.");
                System.err.println("input " + size + "\t" + Math.abs(max));// + "\t" + Math.abs(max) + "\t" + (-max));
                System.err.println(x);
                //System.exit(0);
                throw new IllegalStateException(x);
            } else {
                for (int i = 0; i < maxfiles; i++) {
                    boolean wasSplit = splitRecord(start, files[i], null);
                    if (wasSplit && files.length > 1) {
                        System.err.println("Multiple multi-record Genbank files currently not supported.");
                    } else if (wasSplit) {
                        System.out.println("Split single input file " + files[i].getName() + " into multiple records? " + wasSplit);
                        splitdir = new File(workdir.getAbsolutePath() + "/split_" + files[0].getName());
                        indir = splitdir;
                    } else {
                        System.out.println("Single input file was not split");
                    }
                }
            }
        } else {
            long size = Math.abs(indir.length());
            //System.out.println(size / (1024 * 1024));
            //System.exit(0);
            final long max = Math.abs(2 * 1024 * 1024 * 1024);
            if (size > Math.abs(max)) {
                final String x = "Input file " + indir + " is too large " + (size / (double) (1024 * 1024) + "G. Max allowed size is 2G.");
                System.err.println("input " + size + "\t" + Math.abs(max));
                System.err.println(x);
                //System.exit(0);
                throw new IllegalStateException(x);
            }

            boolean wasSplit = splitRecord(start, indir, null);

            System.out.println("Split single input file into multiple records? " + wasSplit);
            if (wasSplit) {
                splitdir = new File(workdir.getAbsolutePath() + "/split_" + indir.getName());
                indir = splitdir;
                System.out.println("workdir 2 " + workdir.getAbsolutePath());
            }
        }
    }

    /**
     * @param start
     * @throws FileNotFoundException
     */
    private boolean splitRecord(int start, File path, String outpath) throws FileNotFoundException {

        int countfiles = 0;
        boolean split = false;
        Scanner fileScanner = new Scanner(path);
        List<String> locitest = new ArrayList<String>();
        while (fileScanner.hasNextLine()) {
            String cur = fileScanner.nextLine();
            if (!cur.startsWith(" "))
                System.out.println("curtest " + cur);
            if (cur.indexOf("LOCUS") == 0) {
                String curlocus = cur.substring(start, cur.indexOf(" ", start + 1));
                locitest.add(curlocus);
                if (locitest.size() > 1) {
                    break;
                }
            }
        }
        fileScanner.close();

        System.out.println("locitest " + locitest.size());
        if (locitest.size() > 1) {
            if (outpath == null)
                outpath = workdir.getAbsolutePath() + "/split_" + path.getName();
            System.out.println("split outpath " + outpath);
            File splitdir = new File(outpath);
            if (!splitdir.isDirectory()) {
                splitdir.mkdir();
            }

            Scanner fileScanner2 = new Scanner(path);
            List<String> loci = new ArrayList<String>();
            StringBuilder sb = new StringBuilder("");
            while (fileScanner2.hasNextLine() && countfiles < MAX_ALLOWED_FILES) {
                String cur = fileScanner2.nextLine();
                if (!cur.startsWith(" "))
                    System.out.println(cur);
                if (cur.indexOf("LOCUS") == 0) {
                    String curlocus = cur.substring(start, cur.indexOf(" ", start + 1));
                    System.out.println("loci add " + curlocus);
                    loci.add(curlocus);
                    sb.append(cur).append("\n");
                } else if (cur.indexOf("//") == 0) {
                    sb.append(cur).append("\n");
                    System.out.println("loci2 " + loci.size());
                    final int index = loci.size() - 1;
                    System.out.println("loci2 " + loci.size() + "\t" + index);
                    String curoutpath = outpath + "/" + loci.get(index) + ".gbk";
                    try {
                        PrintWriter out = new PrintWriter(new FileWriter(curoutpath));
                        out.print(sb);
                        out.close();
                        split = true;
                        System.out.println("    wrote: " + outpath);
                        countfiles++;
                    } catch (IOException e) {
                        System.err.println("Error creating or writing file " + outpath);
                        System.err.println("IOException: " + e.getMessage());
                    }

                    sb = new StringBuilder("");
                } else {
                    sb.append(cur).append("\n");
                }
            }


            if (countfiles == MAX_ALLOWED_FILES && fileScanner2.hasNextLine()) {
                final String outpath2 = (workdir != null ? workdir + "/" : "") + "README.txt";
                System.out.println("writing " + outpath2);
                try {
                    File outf = new File(outpath2);
                    PrintWriter pw = new PrintWriter(outf);

                    String readmestr = "The limit for uploading is " + MAX_ALLOWED_FILES + " contigs. This download had more than " + MAX_ALLOWED_FILES
                            + " contigs, however only the first " + MAX_ALLOWED_FILES + " will be uploaded.";
                    pw.print(readmestr);
                    pw.close();
                } catch (FileNotFoundException e) {
                    System.err.println("failed to write output " + outpath);
                    e.printStackTrace();
                }
            }

            fileScanner.close();
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
        System.out.println("parseAllInDir " + dir.getAbsolutePath());
        if (dir.isDirectory()) {
            long size = 0;
            for (File f : dir.listFiles()) {
                size += Math.abs(f.length());
            }
            final long max = Math.abs(2 * 1024 * 1024 * 1024);
            if (size > Math.abs(max)) {
                final String x = "Inputs are too large " + (size / (double) (1024 * 1024) + "G. Max allowed size is 2G.");
                System.err.println("input " + size + "\t" + Math.abs(max));
                System.err.println(x);
                //System.exit(0);
                throw new IllegalStateException(x);
            } else {
                for (File f : dir.listFiles()) {
                    //System.out.println("parseAllInDir file " + f.getAbsolutePath());
                    if (f.isDirectory()) {
                        parseAllInDir(pos, f, wc, wsname, http, isTestThis);
                    } else if (f.getName().matches("^.*\\.(gb|gbk|genbank|gbf|gbff)$")) {
                        files.add(f);
                        System.out.println("Added from dir " + f + "\ttotal " + files.size());
                    }
                }
            }
        } else {
            files.add(dir);
            System.out.println("Added from file " + dir);
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
        System.out.println("[" + (pos[0]++) + "] input dir " + dir.getName() + "\tfirst file " + gbkFiles.get(0));
        long time = System.currentTimeMillis();
        //System.out.println("parseGenome "+wsname);
        //ArrayList ar = GbkUploader.uploadGbk(gbkFiles, wsname, dir.getName(), true);
        String name = gbkFiles.get(0).getName();
        final int endIndex = name.lastIndexOf(".");
        name = name.substring(0, endIndex != -1 ? endIndex : name.length());
        System.out.println("parseGenome " + name);
        ArrayList ar = GbkUploader.uploadGbk(gbkFiles, wsname, name, true);

        Genome genome = (Genome) ar.get(2);

      /*  List<Feature> features = genome.getFeatures();
        for (int i = 0; i < features.size(); i++) {
            Feature cur = features.get(i);
            System.out.println("parseGenome "+i + "\t" + cur.getAliases());
        }*/

        genome.setAdditionalProperties("SOURCE", "KBASE_USER_UPLOAD");
        String outpath = workdir + "/" + out_object_g + ".jsonp";

        System.out.println("workdir " + workdir + "\nout_object_g " + out_object_g + "\tout_object_c " + out_object_c);
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
                out_object_c = out_object_g + "_ContigSet";//out_object_g.substring(start, endIndex != -1 ? endIndex : out_object_g.length());
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

            //try {
            out.print(UObject.transformObjectToString(contigSet));
            //} catch (OutOfMemoryError E) {
            //    System.err.println("out of memory error");
            //}
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
        if (out.length() > 0)
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


                if (isTestThis) {
                    System.out.println("using test mode");
                    AuthToken at = ((AuthUser) AuthService.login(user, pwd)).getToken();
                    wc = new WorkspaceClient(new URL(http), at);
                } else {
                    wc = new WorkspaceClient(new URL(http), new AuthToken(kbtok));
                }

                wc.setAuthAllowedForHttp(true);


                String cname = contigSetId;
                if (out_object_c != null) {
                    cname = out_object_c;
                }
                cname = sanitizeObjectName(cname);

                boolean saved2 = false;
                int retry2 = 0;
                try {
                    System.out.println("saving ContigSet " + cname);
                    wc.saveObjects(new SaveObjectsParams().withWorkspace(wsname)
                            .withObjects(Arrays.asList(new ObjectSaveData().withName(cname)
                                    .withType("KBaseGenomes.ContigSet").withData(new UObject(contigSet)))));
                    saved2 = true;
                    System.out.println("successfully saved object");
                /*TODO add shock reference*/
                    //genome.setContigsetRef(contignode.getId().getId());
                } catch (ServerException e) {
                    System.err.println(e.getData());
                    DateFormat dateFormat = new SimpleDateFormat("yyyy/MM/dd HH:mm:ss");
                    Date date = new Date();
                    System.err.println(dateFormat.format(date));

                    retry2++;
                    Thread.sleep(2000);
                    System.err.println("Error saving ContigSet to workspace.");
                    e.printStackTrace();
                } catch (Exception e) {
                    retry2++;
                    Thread.sleep(2000);
                    System.err.println("Error saving ContigSet to workspace.");
                    DateFormat dateFormat = new SimpleDateFormat("yyyy/MM/dd HH:mm:ss");
                    Date date = new Date();
                    System.err.println(dateFormat.format(date));
                    e.printStackTrace();
                }


                genome.setContigsetRef(wsname + "/" + cname);
                String gname = contigSetId;
                if (out_object_g != null) {
                    gname = out_object_g;
                }
                gname = sanitizeObjectName(gname);
                System.out.println("saving Genome " + gname + "\t:" + genome.getContigsetRef() + ":");

                boolean saved = false;
                int retry = 0;
                while (!saved && retry < 10) {
                    try {
                        wc.saveObjects(new SaveObjectsParams().withWorkspace(wsname)
                                .withObjects(Arrays.asList(new ObjectSaveData().withName(gname).withMeta(meta)
                                        .withType("KBaseGenomes.Genome").withData(new UObject(genome)))));
                        saved = true;
                    } catch (ServerException e) {
                        System.err.println(e.getData());
                        DateFormat dateFormat = new SimpleDateFormat("yyyy/MM/dd HH:mm:ss");
                        Date date = new Date();
                        System.err.println(dateFormat.format(date));

                        retry2++;
                        Thread.sleep(2000);
                        System.err.println("Error saving ContigSet to workspace.");
                        e.printStackTrace();
                    } catch (Exception e) {
                        retry2++;
                        Thread.sleep(2000);
                        System.err.println("Error saving ContigSet to workspace.");
                        DateFormat dateFormat = new SimpleDateFormat("yyyy/MM/dd HH:mm:ss");
                        Date date = new Date();
                        System.err.println(dateFormat.format(date));
                        e.printStackTrace();
                    }
                }

                System.out.println("successfully saved object");

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
