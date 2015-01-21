package us.kbase.genbank;

import us.kbase.common.service.Tuple11;
import us.kbase.kbasegenomes.ContigSet;
import us.kbase.kbasegenomes.Genome;
import us.kbase.workspace.ObjectData;
import us.kbase.workspace.ObjectIdentity;
import us.kbase.workspace.SaveObjectsParams;

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

/**
 * Created by Marcin Joachimiak
 * User: marcin
 * Date: 11/3/14
 * Time: 3:00 PM
 */
public class ValidateGBK {


    File indir = null;

    String[] argsPossible = {"-i", "--input_file_name"};
    String[] argsPossibleMap = {"input", "input"};


    /**
     * @param args
     * @throws Exception
     */
    public ValidateGBK(String[] args) throws Exception {

        for (int i = 0; i < args.length; i++) {
            int index = Arrays.binarySearch(argsPossible, args[i]);//Arrays.asList(argsPossible).indexOf(args[i]);
            System.out.println(index);
            if (index > -1 && argsPossibleMap[index].equals("input")) {
                indir = new File(args[i + 1]);
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
        });
    }


    /**
     * @param pos
     * @param dir
     * @param wc
     * @throws Exception
     */
    public static void parseAllInDir(int[] pos, File dir, ObjectStorage wc) throws Exception {

        List<File> files = new ArrayList<File>();
        if(dir.isDirectory()) {
        for (File f : dir.listFiles()) {
            if (f.isDirectory()) {
                parseAllInDir(pos, f, wc);
            } else if (f.getName().matches("^.*\\.(gb|gbk|genbank|gbff)$")) {//if (f.getName().endsWith(".gbk")) {
                files.add(f);
                System.err.println("Added " + f);
            }
        }
        }
        else {
            files.add(dir);
        }
        if (files.size() > 0)
            parseGenome(pos, dir, files, wc);

    }

    /**
     * @param pos
     * @param dir
     * @param gbkFiles
     * @param wc
     * @throws Exception
     */
    public static void parseGenome(int[] pos, File dir, List<File> gbkFiles, ObjectStorage wc) { //throws Exception
        System.out.println("[" + (pos[0]++) + "] " + dir.getName());
        long time = System.currentTimeMillis();
        try {
            ArrayList ar = GbkUploader.uploadGbk(gbkFiles, "replacewithrealWS", dir.getName(), true);

            /*ar.add(ws);
            ar.add(id);
            ar.add(genome);
            ar.add(contigSetId);
            ar.add(contigSet);
            ar.add(meta);*/

            Genome gnm = (Genome) ar.get(2);

            ContigSet cs = (ContigSet) ar.get(4);
        } catch (Exception e) {
            System.err.print(e.getMessage());
            System.err.print(e.getStackTrace());
            e.printStackTrace();
        }

    }

    /**
     * @param args
     */
    public final static void main(String[] args) {
        if (args.length == 2) {
            try {
                ValidateGBK vg = new ValidateGBK(args);
            } catch (Exception e) {
                e.printStackTrace();
            }
        } else {
            /*TODO separate input file and input dir args*/
            //System.out.println("usage: java us.kbase.genbank.ValidateGBK <dir or dir of dirs with GenBank .gbk files>");// <convert y/n> <save y/n>");
            System.out.println("usage: java us.kbase.genbank.ConvertGBK <-i or --input_file_name file or dir or files of GenBank .gbk files>");// <convert y/n> <save y/n>");
        }
    }

}
