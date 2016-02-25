package us.kbase.kbaseenigmametals;

import java.io.File;
import us.kbase.common.service.UObject;
import us.kbase.kbaseenigmametals.ChromatographyMatrix;
import us.kbase.kbaseenigmametals.ChromatographyMatrixUploader;

public class ChromatographyDataImporter {

	private String fileName = null;
	private String token = null;
	private Long workspaceId = null;

	
	public ChromatographyDataImporter (String fileName, Long workspaceId, String token) throws Exception{
		if (fileName == null) {
			System.out.println("cMonkey Expression data file name required");
		} else {
			this.fileName = fileName;
		}
		if (token == null) {
			throw new Exception("Token not assigned");
		} else {
			this.token = token;
		}
		
		if (workspaceId == null) {
			throw new Exception("Workspace name not assigned");
		} else {
			this.workspaceId = workspaceId;
		}

	}
	
	public void importMatrix (String matrixName) throws Exception {
		
		ChromatographyMatrixUploader uploader = new ChromatographyMatrixUploader();
		
		ChromatographyMatrix matrix = new ChromatographyMatrix();
		matrix.setName(matrixName);
		
		File inputFile = new File(this.fileName);
		
		matrix = uploader.generateChromatographyMatrix(inputFile, matrix);
		//System.out.println(matrix.toString());
		WsDeluxeUtil.saveObjectToWorkspaceRef(UObject.transformObjectToObject(matrix, UObject.class), "KBaseEnigmaMetals.ChromatographyMatrix", workspaceId, matrixName, "https://ci.kbase.us/services/ws", token.toString());
	}
	

}
