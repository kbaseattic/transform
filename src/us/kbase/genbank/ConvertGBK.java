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

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
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
            "-w", "--workspace_name", "-wu", "--workspace_url", "-su", "--shock_url", "-wd", "--working_directory"};
    String[] argsPossibleMap = {"input", "input", "outputg", "outputg", "outputc", "outputc",
            "wsn", "wsn", "wsu", "wsu", "shocku", "shocku", "wd", "wd"};

    static String wsurl = null;
    static String shockurl = null;

    String wsname = null;

    String workdir;

    String outfileg = null;
    String outfilec = null;
    File indir;


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
                    outfileg = args[i + 1];
                } else if (argsPossibleMap[index].equals("outputc")) {
                    outfilec = args[i + 1];
                } else if (argsPossibleMap[index].equals("wsn")) {
                    wsname = args[i + 1];
                } else if (argsPossibleMap[index].equals("wsu")) {
                    wsurl = args[i + 1];
                } else if (argsPossibleMap[index].equals("shocku")) {
                    shockurl = args[i + 1];
                } else if (argsPossibleMap[index].equals("wd")) {
                    workdir = args[i + 1];
                }
            }
        }

        if (workdir == null) {
            File tmpf = new File("./");
            workdir = tmpf.getAbsolutePath();
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
                } else if (f.getName().matches("^.*\\.(gb|gbk|genbank|gbff)$")) {
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
        ArrayList ar = GbkUploader.uploadGbk(gbkFiles, wsname, dir.getName(), true);

        Genome genome = (Genome) ar.get(2);
        genome.setAdditionalProperties("SOURCE", "KBASE_USER_UPLOAD");
        String outpath = workdir + "/" + outfileg;
        if (outfileg == null)
            outpath = workdir + "/" + outfileg + ".jsonp";
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

        String outpath2 = workdir + "/" + outfilec;//contigId + ".jsonp";

        if (outfilec == null)
            outpath2 = workdir + "/" + genome.getId() + "_ContigSet" + ".jsonp";
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

        genome.setMd5(globalmd5);

        if (wsname != null) {

            /*ar.add(ws);
            ar.add(id);
            ar.add(genome);
            ar.add(contigSetId);
            ar.add(contigSet);
            ar.add(meta);*/

            String genomeid = (String) ar.get(1);

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
                    AuthToken at = ((AuthUser) AuthService.login(user, pwd)).getToken();
                    wc = new WorkspaceClient(new URL(http), at);
                } else {
                    wc = new WorkspaceClient(new URL(http), new AuthToken(kbtok));
                }

                wc.setAuthAllowedForHttp(true);

                /*TODO create provenance string --- uploaded by transform service, user*/
                try {
                    wc.saveObjects(new SaveObjectsParams().withWorkspace(wsname)
                            .withObjects(Arrays.asList(new ObjectSaveData().withName(contigSetId)
                                    .withType("KBaseGenomes.ContigSet").withData(new UObject(contigSet)))));

                /*TODO add workspace reference*/
                    //genome.setContigsetRef(contignode.getId().getId());
                } catch (IOException e) {
                    System.err.println("Error saving ContigSet to workspace, data may be too large (IOException)).");
                    e.printStackTrace();
                } catch (JsonClientException e) {
                    System.err.println("Error saving ContigSet to workspace, data may be too large (JsonClientException).");
                    e.printStackTrace();
                }

                wc.saveObjects(new SaveObjectsParams().withWorkspace(wsname)
                        .withObjects(Arrays.asList(new ObjectSaveData().withName(genomeid).withMeta(meta)
                                .withType("KBaseGenomes.Genome").withData(new UObject(genome)))));

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

        System.out.println("    time: " + (System.currentTimeMillis() - time) + " ms");
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
        if (args.length == 2 || args.length == 4 || args.length == 6 || args.length == 8 || args.length == 10 || args.length == 12) {
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
                    "<-w or --ws_name ws name> " +// <convert y/n> <save y/n>");
                    "<-wu or --ws_url ws url> " +// <convert y/n> <save y/n>");
                    "<-su or --shock_url shock url> " +
                    "<-wd or --working_directory");// <convert y/n> <save y/n>");

            //--workspace_service_url {0}--workspace_name {1} --object_name {2} --contigset_object_name {3} "
        }
    }

}
