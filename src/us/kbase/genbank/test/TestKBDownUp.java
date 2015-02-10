package us.kbase.genbank.test;

import us.kbase.auth.AuthService;
import us.kbase.auth.AuthToken;
import us.kbase.auth.AuthUser;
import us.kbase.common.service.Tuple11;
import us.kbase.genbank.ConvertGBK;
import us.kbase.genbank.GenometoGbk;
import us.kbase.workspace.ListObjectsParams;
import us.kbase.workspace.WorkspaceClient;

import java.io.File;
import java.net.URL;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

/**
 * Created by Marcin Joachimiak
 * User: marcin
 * Date: 2/2/15
 * Time: 11:38 PM
 */
public class TestKBDownUp {
    boolean isTest;

    String[] argsPossible = {"-w", "--workspace_name", "-wu", "--workspace_service_url", "-su", "--shock_url", "-wd", "--working_directory", "--test"};
    String[] argsPossibleMap = {"wsn", "wsn", "wsu", "wsu", "shocku", "shocku", "wd", "wd", "t"};

    String wsname, shockurl, wsurl;
    File workdir;

    int skip =10000;

    /**
     * @param args
     */
    public TestKBDownUp(String[] args) {

        for (int i = 0; i < args.length; i++) {
            int index = Arrays.asList(argsPossible).indexOf(args[i]);
            if (index > -1) {
                if (argsPossibleMap[index].equals("wsn")) {
                    wsname = args[i + 1];
                } else if (argsPossibleMap[index].equals("wsu")) {
                    wsurl = args[i + 1];
                } else if (argsPossibleMap[index].equals("shocku")) {
                    shockurl = args[i + 1];
                } else if (argsPossibleMap[index].equals("wd")) {
                    workdir = new File(args[i + 1]);
                } else if (argsPossibleMap[index].equals("t")) {
                    if (args[i + 1].equalsIgnoreCase("Y") || args[i + 1].equalsIgnoreCase("yes")
                            || args[i + 1].equalsIgnoreCase("T") || args[i + 1].equalsIgnoreCase("TRUE"))
                        isTest = true;
                }
            }
        }

        if (workdir == null) {
            workdir = new File(Paths.get(".").toAbsolutePath().normalize().toString());
        } else if (!workdir.exists()) {
            workdir.mkdirs();
        }

        try {
            WorkspaceClient wc = null;

            String user = System.getProperty("test.user");
            String pwd = System.getProperty("test.pwd");

            String kbtok = System.getenv("KB_AUTH_TOKEN");

            if (isTest) {
                System.out.println("using test mode");
                AuthToken at = ((AuthUser) AuthService.login(user, pwd)).getToken();
                wc = new WorkspaceClient(new URL(wsurl), at);
            } else {
                wc = new WorkspaceClient(new URL(wsurl), new AuthToken(kbtok));
            }

            wc.setAuthAllowedForHttp(true);


            int MAX = 30000;
            for (int m = skip; m < MAX; m += 1000) {
                ListObjectsParams lop = new ListObjectsParams();

                List<String> lw = new ArrayList();
                lw.add("KBasePublicGenomesV5");
                lop.withType("KBaseGenomes.Genome").withWorkspaces(lw);
                lop.withSkip((long) m);

                List<Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>>> getobj =
                        wc.listObjects(lop);

                System.out.println("got data for " + getobj.size() + " objects, skip " + m);

                int count = 0;
                for (Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>> t : getobj) {
                    System.out.println(count + "\t" + t.getE2() + "\t" + ((double) t.getE10() / (double) (1024 ^ 2)) + "M");
                    count++;

                    List<String> ar = new ArrayList();
                    List<String> ar2 = new ArrayList();
                    try {

                        ar.add("--workspace_name");
                        ar.add("KBasePublicGenomesV5");
                        ar.add("--workspace_service_url");
                        ar.add("https://kbase.us/services/ws");
                        ar.add("--object_name");
                        ar.add(t.getE2());
                        ar.add("--working_directory");
                        final String cleangenomeid = t.getE2().replace('|', '_');
                        ar.add(workdir.getAbsolutePath() + "/" + cleangenomeid);

                        if (isTest) {
                            ar.add("--test");
                            ar.add("T");
                        }
                        String[] argsgt = new String[ar.size()];
                        int count2 = 0;
                        for (Object obj : ar) {
                            argsgt[count2] = obj.toString();
                            count2++;
                        }

                        GenometoGbk gt = new GenometoGbk(wc);
                        gt.init(argsgt);
                        gt.run();

                        //String[] argsPossible = {"-i", "--input_directory", "-o", "--object_name", "-oc", "--contigset_object_name",
                        //"-w", "--workspace_name", "-wu", "--workspace_service_url", "-su", "--shock_url", "-wd", "--working_directory", "--test"};

                        ar2.add("--workspace_name");
                        ar2.add("upload_testing");
                        ar2.add("--workspace_service_url");
                        ar2.add("https://kbase.us/services/ws");
                        ar2.add("--input_directory");
                        ar2.add(workdir.getAbsolutePath() + "/" + cleangenomeid);
                        ar2.add("--working_directory");
                        ar2.add(workdir.getAbsolutePath() + "/" + cleangenomeid);

                        if (isTest) {
                            ar2.add("--test");
                            ar2.add("T");
                        }
                        String[] argsgt2 = new String[ar2.size()];
                        int count22 = 0;
                        for (Object obj : ar2) {
                            argsgt2[count22] = obj.toString();
                            count22++;
                        }

                        ConvertGBK cg = new ConvertGBK(wc);
                        cg.init(argsgt2);
                        try {
                            cg.run();
                            File tobermed = new File(workdir.getAbsolutePath() + "/" + cleangenomeid);
                            rmdir(tobermed);
                        } catch (Exception e) {
                            e.printStackTrace();
                        }

                    } catch (Exception e) {
                        System.out.println("Error for genome " + t.getE2());

                        String cmd1 = "";
                        int count4 = 0;
                        for (String s : ar) {
                            cmd1 += s;
                            if (count4 < ar.size() - 1)
                                cmd1 += ",";
                            count4++;
                        }

                        String cmd2 = "";
                        int count5 = 0;
                        for (String s : ar2) {
                            cmd2 += s;
                            if (count5 < ar2.size() - 1)
                                cmd2 += ",";
                            count5++;
                        }

                        System.out.println("Error down " + cmd1);
                        System.out.println("Error up " + cmd2);
                        e.printStackTrace();
                    }

                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }


    }

    /**
     * @param dir
     * @return
     */
    public static boolean rmdir(File dir) {
        if (dir.isDirectory()) {
            String[] child = dir.list();
            for (int i = 0; i < child.length; i++) {
                boolean success = rmdir(new File(dir, child[i]));
                if (!success) {
                    return false;
                }
            }
        }

        return dir.delete(); // The directory is empty now and can be deleted.
    }


    /**
     * @param args
     */
    public final static void main(String[] args) {
        if (args.length >= 4 || args.length <= 10) {
            try {
                TestKBDownUp clt = new TestKBDownUp(args);
            } catch (Exception e) {
                e.printStackTrace();
            }
        } else {
            System.out.println("usage: java us.kbase.genbank.test.TestKBDownUp " +
                    "<-w or --workspace_name ws name> " +
                    "<-wu or --workspace_service_url ws url> " +
                    "<-su or --shock_url shock url> " +
                    "<-wd or --working_directory> " +
                    "<--test>");
        }
    }
}
